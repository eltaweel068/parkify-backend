using Microsoft.AspNetCore.Mvc;
using Parkify.API.Data;
using Parkify.API.Services;
using Parkify.API.WebSockets;
using Microsoft.EntityFrameworkCore;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/iot")]
public class IoTController(
    AppDbContext db,
    ParkingService parkingService,
    BookingService bookingService,
    AlertService alertService,
    NotificationService notificationService,
    VehicleLogService vehicleLogService,
    ConnectionManager wsManager) : ControllerBase
{
    private async Task<bool> ValidateKeyAsync(Guid parkingId, string deviceKey)
    {
        var parking = await db.Parkings.FindAsync(parkingId);
        return parking?.DeviceKey == deviceKey;
    }

    [HttpGet("parking-status")]
    public async Task<IActionResult> ParkingStatus(
        [FromQuery(Name = "parking_id")] Guid parkingId,
        [FromQuery(Name = "device_key")] string deviceKey)
    {
        if (!await ValidateKeyAsync(parkingId, deviceKey))
            return StatusCode(403, new { detail = "Invalid device key" });

        var parking = await db.Parkings.FindAsync(parkingId);
        if (parking == null) return NotFound(new { detail = "Parking not found" });

        await parkingService.SyncCapacityAsync(parkingId);

        return Ok(new
        {
            success = true,
            parking_id = parkingId,
            total_slots = parking.TotalSlots,
            occupied_slots = parking.OccupiedSlots,
            available_slots = parking.AvailableSlots,
            is_full = parking.IsFull
        });
    }

    [HttpPost("plate-detect")]
    public async Task<IActionResult> PlateDetect(
        [FromQuery(Name = "parking_id")] Guid parkingId,
        [FromQuery] string plate,
        [FromQuery] string action = "entry",
        [FromQuery] string gate = "Gate A",
        [FromQuery] double confidence = 0.95,
        [FromQuery(Name = "device_key")] string deviceKey = "")
    {
        if (!await ValidateKeyAsync(parkingId, deviceKey))
            return StatusCode(403, new { detail = "Invalid device key" });

        var log = await vehicleLogService.AddLogAsync(parkingId, plate, action, gate, confidence);

        bool verified = false;
        Guid? bookingId = null;
        string gateCommand = "none";
        string message = "";

        if (action == "entry")
        {
            var booking = await bookingService.FindByPlateAsync(parkingId, plate, new[] { "confirmed" });
            if (booking != null)
            {
                verified = true;
                bookingId = booking.Id;
                gateCommand = "open";
                message = $"Vehicle verified. Booking {booking.Id} checked in.";
                await bookingService.CheckInAsync(booking.Id);
                await wsManager.SendToChannelAsync($"gate:{parkingId}", new { type = "gate_command", gate_type = "entry", action = "open" });
            }
            else
            {
                message = $"Unregistered vehicle {plate} at {gate}. No matching booking found.";
                await alertService.CreateAsync(parkingId, "security", "medium",
                    $"Unregistered vehicle detected: {plate} at {gate} (confidence: {confidence})");
            }
        }
        else if (action == "exit")
        {
            var booking = await bookingService.FindByPlateAsync(parkingId, plate, new[] { "active" });
            if (booking != null)
            {
                verified = true;
                bookingId = booking.Id;
                gateCommand = "open";
                message = $"Vehicle verified. Booking {booking.Id} checked out.";
                await bookingService.CheckOutAsync(booking.Id);
                await wsManager.SendToChannelAsync($"gate:{parkingId}", new { type = "gate_command", gate_type = "exit", action = "open" });
                await NotifySpotWatchersAsync(parkingId);
            }
            else
            {
                gateCommand = "open";
                message = $"Vehicle {plate} exiting without active booking. Gate opened.";
                await wsManager.SendToChannelAsync($"gate:{parkingId}", new { type = "gate_command", gate_type = "exit", action = "open" });
            }
        }

        await wsManager.SendToChannelAsync("admin", new
        {
            type = "plate_detected",
            parking_id = parkingId,
            data = new { plate, action, gate, confidence, verified, booking_id = bookingId, gate_command = gateCommand }
        });

        return Ok(new { success = true, verified, log_id = log.Id, plate, action, gate_command = gateCommand, booking_id = bookingId, message });
    }

    [HttpPost("fire-alert")]
    public async Task<IActionResult> FireAlert(
        [FromQuery(Name = "parking_id")] Guid parkingId,
        [FromQuery] string message = "Fire detected",
        [FromQuery] double confidence = 0.87,
        [FromQuery(Name = "device_key")] string deviceKey = "")
    {
        if (!await ValidateKeyAsync(parkingId, deviceKey))
            return StatusCode(403, new { detail = "Invalid device key" });

        var alert = await alertService.CreateAsync(parkingId, "fire", "critical",
            $"{message} (confidence: {confidence})");

        await notificationService.BroadcastAsync("Fire Alert!",
            $"Fire detected at {alert.ParkingName}. Please evacuate immediately.", "alert");

        await wsManager.SendToChannelAsync("admin", new
        {
            type = "fire_alert",
            parking_id = parkingId,
            data = new { message, confidence, alert_id = alert.Id }
        });

        return Ok(new { success = true, alert_id = alert.Id });
    }

    [HttpPost("theft-alert")]
    public async Task<IActionResult> TheftAlert(
        [FromQuery(Name = "parking_id")] Guid parkingId,
        [FromQuery] string message = "Suspicious activity detected",
        [FromQuery] double confidence = 0.80,
        [FromQuery(Name = "weapon_type")] string weaponType = "unknown",
        [FromQuery(Name = "device_key")] string deviceKey = "")
    {
        if (!await ValidateKeyAsync(parkingId, deviceKey))
            return StatusCode(403, new { detail = "Invalid device key" });

        var alert = await alertService.CreateAsync(parkingId, "theft", "high",
            $"{message} - weapon: {weaponType} (confidence: {confidence})");

        await notificationService.BroadcastAsync("Security Alert!",
            $"Suspicious activity detected at {alert.ParkingName}. Security has been notified.", "security");

        await wsManager.SendToChannelAsync("admin", new
        {
            type = "theft_alert",
            parking_id = parkingId,
            data = new { message, confidence, weapon_type = weaponType, alert_id = alert.Id }
        });

        return Ok(new { success = true, alert_id = alert.Id });
    }

    [HttpPost("slot-update")]
    public async Task<IActionResult> SlotUpdate(
        [FromQuery(Name = "parking_id")] Guid parkingId,
        [FromQuery(Name = "slot_number")] string slotNumber,
        [FromQuery] string status,
        [FromQuery(Name = "device_key")] string deviceKey = "")
    {
        if (!await ValidateKeyAsync(parkingId, deviceKey))
            return StatusCode(403, new { detail = "Invalid device key" });

        var slot = await db.ParkingSlots.FirstOrDefaultAsync(s => s.ParkingId == parkingId && s.SlotNumber == slotNumber);
        if (slot == null) return NotFound(new { detail = "Slot not found" });

        var oldStatus = slot.Status;
        slot.Status = status;

        var parking = await db.Parkings.FindAsync(parkingId);
        if (parking != null && oldStatus != status)
        {
            if (status == "available" && oldStatus == "occupied")
            {
                parking.AvailableSlots = Math.Min(parking.TotalSlots, parking.AvailableSlots + 1);
                parking.OccupiedSlots = Math.Max(0, parking.OccupiedSlots - 1);
            }
            else if (status == "occupied" && oldStatus == "available")
            {
                parking.AvailableSlots = Math.Max(0, parking.AvailableSlots - 1);
                parking.OccupiedSlots++;
            }
            parking.IsFull = parking.AvailableSlots <= 0;
        }

        await db.SaveChangesAsync();

        if (status == "available" && oldStatus != "available")
            await NotifySpotWatchersAsync(parkingId);

        await wsManager.SendToChannelAsync($"parking:{parkingId}", new
        {
            type = "slot_update",
            slot_id = slot.Id,
            slot_number = slotNumber,
            status
        });
        await wsManager.SendToChannelAsync("admin", new
        {
            type = "slot_update",
            parking_id = parkingId,
            slot_id = slot.Id,
            slot_number = slotNumber,
            status
        });

        var response = new Dictionary<string, object>
        {
            ["success"] = true,
            ["slot_id"] = slot.Id,
            ["status"] = status
        };
        if (parking != null)
        {
            response["occupied_slots"] = parking.OccupiedSlots;
            response["available_slots"] = parking.AvailableSlots;
            response["is_full"] = parking.IsFull;
        }
        return Ok(response);
    }

    [HttpPost("gate-control")]
    public async Task<IActionResult> GateControl(
        [FromQuery(Name = "parking_id")] Guid parkingId,
        [FromQuery(Name = "gate_type")] string gateType = "entry",
        [FromQuery] string action = "open",
        [FromQuery(Name = "device_key")] string deviceKey = "")
    {
        if (!await ValidateKeyAsync(parkingId, deviceKey))
            return StatusCode(403, new { detail = "Invalid device key" });

        await wsManager.SendToChannelAsync($"gate:{parkingId}", new
        {
            type = "gate_command",
            gate_type = gateType,
            action
        });

        return Ok(new { success = true, message = $"Gate {gateType} {action} command sent to {parkingId}" });
    }

    private async Task NotifySpotWatchersAsync(Guid parkingId)
    {
        var watchers = await db.SpotWatchers.Where(w => w.ParkingId == parkingId).ToListAsync();
        if (!watchers.Any()) return;

        var parking = await db.Parkings.FindAsync(parkingId);
        if (parking == null) return;

        var dataJson = System.Text.Json.JsonSerializer.Serialize(new { parking_id = parkingId });
        foreach (var watcher in watchers)
        {
            await notificationService.CreateAsync(
                watcher.UserId,
                "Spot Available!",
                $"A parking spot just opened up at {parking.Name}. Book now!",
                "booking",
                dataJson);
        }
        db.SpotWatchers.RemoveRange(watchers);
        await db.SaveChangesAsync();
    }
}
