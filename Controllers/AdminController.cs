using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Services;
using Microsoft.EntityFrameworkCore;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/admin")]
[Authorize(Roles = "admin")]
public class AdminController(
    AppDbContext db,
    ParkingService parkingService,
    AlertService alertService,
    VehicleLogService vehicleLogService,
    NotificationService notificationService,
    SupportService supportService) : ControllerBase
{
    private Guid UserId => Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    // ─── Dashboard ────────────────────────────────────────────

    [HttpGet("dashboard")]
    public async Task<IActionResult> Dashboard()
    {
        var parkings = await db.Parkings.Where(p => p.IsActive).ToListAsync();
        var totalSlots = parkings.Sum(p => p.TotalSlots);
        var available = parkings.Sum(p => p.AvailableSlots);
        var occupied = parkings.Sum(p => p.OccupiedSlots);

        var today = DateTime.SpecifyKind(DateTime.UtcNow.Date, DateTimeKind.Utc);
        var todayBookings = await db.Bookings.CountAsync(b => b.CreatedAt >= today);
        var activeBookings = await db.Bookings.CountAsync(b => b.Status == "confirmed" || b.Status == "active");
        var todayRevenue = await db.Bookings
            .Where(b => b.CreatedAt >= today && b.PaymentStatus == "completed")
            .SumAsync(b => (double?)b.TotalAmount) ?? 0;
        var totalUsers = await db.Users.CountAsync();
        var pendingAlerts = await alertService.GetActiveCountAsync();

        return Ok(new DashboardStats
        {
            TotalParkings = parkings.Count,
            TotalSlots = totalSlots,
            AvailableSlots = available,
            OccupiedSlots = occupied,
            TotalUsers = totalUsers,
            ActiveBookings = activeBookings,
            TodayBookings = todayBookings,
            TodayRevenue = Math.Round(todayRevenue, 2),
            PendingAlerts = pendingAlerts,
            Currency = "EGP"
        });
    }

    // ─── Gate Control ─────────────────────────────────────────

    [HttpPost("gates/{parkingId}/control")]
    public async Task<IActionResult> GateControl(Guid parkingId, [FromBody] GateControlRequest req)
    {
        var parking = await db.Parkings.FindAsync(parkingId);
        if (parking == null) return NotFound(new { detail = "Parking not found" });
        return Ok(new { success = true, message = $"Gate {req.GateType} {req.Action} sent", parking_id = parkingId });
    }

    // ─── Bookings ─────────────────────────────────────────────

    [HttpGet("bookings")]
    public async Task<IActionResult> AllBookings([FromQuery] string? status = null) =>
        Ok(await new BookingService(db).GetAllAsync(status));

    [HttpPost("bookings/{bookingId}/cancel")]
    public async Task<IActionResult> AdminCancelBooking(Guid bookingId)
    {
        var booking = await db.Bookings
            .Include(b => b.Slot)
            .Include(b => b.Parking)
            .FirstOrDefaultAsync(b => b.Id == bookingId);
        if (booking == null) return NotFound(new { detail = "Booking not found" });
        if (booking.Status == "active")
            return BadRequest(new { detail = "Cannot cancel an active booking. Check out first." });
        if (booking.Status is "completed" or "cancelled")
            return BadRequest(new { detail = $"Booking is already {booking.Status}" });

        booking.Status = "cancelled";
        booking.Slot.Status = "available";
        booking.Parking.AvailableSlots = Math.Min(booking.Parking.TotalSlots, booking.Parking.AvailableSlots + 1);
        booking.Parking.OccupiedSlots = Math.Max(0, booking.Parking.OccupiedSlots - 1);
        booking.Parking.IsFull = false;
        await db.SaveChangesAsync();

        return Ok(await new BookingService(db).GetByIdAsync(bookingId));
    }

    [HttpPost("bookings/{bookingId}/check-in")]
    public async Task<IActionResult> AdminCheckIn(Guid bookingId)
    {
        var result = await new BookingService(db).CheckInAsync(bookingId);
        if (result == null) return BadRequest(new { detail = "Booking not found or not in confirmed status" });
        return Ok(result);
    }

    [HttpPost("bookings/{bookingId}/check-out")]
    public async Task<IActionResult> AdminCheckOut(Guid bookingId)
    {
        var result = await new BookingService(db).CheckOutAsync(bookingId);
        if (result == null) return BadRequest(new { detail = "Booking not found or not in active status" });
        return Ok(result);
    }

    // ─── Users ────────────────────────────────────────────────

    [HttpGet("users")]
    public async Task<IActionResult> AllUsers()
    {
        var users = await db.Users.Select(u => new
        {
            u.Id, u.Email, u.Name, u.FirstName, u.LastName,
            u.Phone, u.Role, u.IsActive, u.Gender, u.Address,
            u.CreatedAt
        }).ToListAsync();
        return Ok(users);
    }

    [HttpGet("users/{userId}")]
    public async Task<IActionResult> GetUser(Guid userId)
    {
        var user = await db.Users.Select(u => new
        {
            u.Id, u.Email, u.Name, u.FirstName, u.LastName,
            u.Phone, u.Role, u.IsActive, u.Gender, u.Address,
            u.CreatedAt
        }).FirstOrDefaultAsync(u => u.Id == userId);
        if (user == null) return NotFound(new { detail = "User not found" });
        return Ok(user);
    }

    [HttpPut("users/{userId}/suspend")]
    public async Task<IActionResult> SuspendUser(Guid userId, [FromBody] UserStatusUpdateRequest req)
    {
        var user = await db.Users.FindAsync(userId);
        if (user == null) return NotFound(new { detail = "User not found" });
        if (user.Role == "admin") return BadRequest(new { detail = "Cannot modify admin accounts" });

        user.IsActive = req.IsActive;
        if (!req.IsActive && !string.IsNullOrEmpty(req.Reason))
        {
            await notificationService.CreateAsync(userId, "Account Suspended",
                $"Your account has been suspended. Reason: {req.Reason}", "security");
        }
        await db.SaveChangesAsync();
        var status = req.IsActive ? "activated" : "suspended";
        return Ok(new { success = true, user_id = userId, status, is_active = req.IsActive });
    }

    [HttpDelete("users/{userId}")]
    public async Task<IActionResult> DeleteUser(Guid userId)
    {
        var user = await db.Users.FindAsync(userId);
        if (user == null) return NotFound(new { detail = "User not found" });
        if (user.Role == "admin") return BadRequest(new { detail = "Cannot delete admin accounts" });
        db.Users.Remove(user);
        await db.SaveChangesAsync();
        return Ok(new { success = true, message = $"User {userId} deleted" });
    }

    // ─── Alerts ───────────────────────────────────────────────

    [HttpGet("alerts")]
    public async Task<IActionResult> GetAlerts([FromQuery] string? status = null) =>
        Ok(await alertService.GetAllAsync(status));

    [HttpGet("alerts/{alertId}")]
    public async Task<IActionResult> GetAlert(Guid alertId)
    {
        var alert = await alertService.GetByIdAsync(alertId);
        if (alert == null) return NotFound(new { detail = "Alert not found" });
        return Ok(alert);
    }

    [HttpPut("alerts/{alertId}/acknowledge")]
    public async Task<IActionResult> AcknowledgeAlert(Guid alertId)
    {
        var alert = await alertService.AcknowledgeAsync(alertId);
        if (alert == null) return NotFound(new { detail = "Alert not found" });
        return Ok(alert);
    }

    [HttpPut("alerts/{alertId}/resolve")]
    public async Task<IActionResult> ResolveAlert(Guid alertId)
    {
        var alert = await alertService.ResolveAsync(alertId, UserId);
        if (alert == null) return NotFound(new { detail = "Alert not found" });
        return Ok(alert);
    }

    // ─── Vehicle Logs ─────────────────────────────────────────

    [HttpGet("vehicles/logs")]
    public async Task<IActionResult> GetVehicleLogs(
        [FromQuery(Name = "parking_id")] Guid? parkingId = null,
        [FromQuery] string? action = null,
        [FromQuery] int limit = 50)
    {
        return Ok(await vehicleLogService.GetLogsAsync(parkingId, action, limit));
    }

    // ─── Notifications ────────────────────────────────────────

    [HttpPost("notifications/send")]
    public async Task<IActionResult> SendNotification([FromBody] AdminSendNotificationRequest req)
    {
        if (req.UserId.HasValue)
        {
            var user = await db.Users.FindAsync(req.UserId);
            if (user == null) return NotFound(new { detail = "User not found" });
            var notif = await notificationService.CreateAsync(req.UserId.Value, req.Title, req.Message, req.NotificationType);
            return Ok(new { success = true, message = "Notification sent", notification_id = notif.Id });
        }
        else
        {
            var count = await notificationService.BroadcastAsync(req.Title, req.Message, req.NotificationType);
            return Ok(new { success = true, message = $"Notification broadcast to {count} users" });
        }
    }

    // ─── Support Tickets ──────────────────────────────────────

    [HttpGet("support/tickets")]
    public async Task<IActionResult> GetAllTickets() => Ok(await supportService.GetAllAsync());

    [HttpPut("support/tickets/{ticketId}/status")]
    public async Task<IActionResult> UpdateTicketStatus(Guid ticketId, [FromQuery] string status)
    {
        var ticket = await supportService.UpdateStatusAsync(ticketId, status);
        if (ticket == null) return NotFound(new { detail = "Ticket not found" });
        return Ok(ticket);
    }

    // ─── Parking Management ───────────────────────────────────

    [HttpGet("parkings")]
    public async Task<IActionResult> AdminGetParkings() =>
        Ok(await parkingService.GetAllAsync());

    [HttpPost("parkings")]
    public async Task<IActionResult> CreateParking([FromBody] ParkingCreateRequest req) =>
        Ok(await parkingService.CreateAsync(req));

    [HttpPut("parkings/{parkingId}")]
    public async Task<IActionResult> UpdateParking(Guid parkingId, [FromBody] ParkingUpdateRequest req)
    {
        var p = await parkingService.UpdateAsync(parkingId, req);
        if (p == null) return NotFound(new { detail = "Parking not found" });
        return Ok(p);
    }

    [HttpDelete("parkings/{parkingId}")]
    public async Task<IActionResult> DeleteParking(Guid parkingId)
    {
        if (!await parkingService.DeleteAsync(parkingId))
            return NotFound(new { detail = "Parking not found" });
        return Ok(new { success = true, message = $"Parking {parkingId} deactivated" });
    }

    [HttpGet("parkings/{parkingId}/slots")]
    public async Task<IActionResult> GetSlots(Guid parkingId)
    {
        var p = await parkingService.GetByIdAsync(parkingId);
        if (p == null) return NotFound(new { detail = "Parking not found" });
        return Ok(await parkingService.GetSlotsAsync(parkingId));
    }
}
