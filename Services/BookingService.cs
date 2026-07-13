using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class BookingService(AppDbContext db)
{
    public async Task<BookingResponse> CreateAsync(Guid userId, BookingCreateRequest req)
    {
        var parking = await db.Parkings.FindAsync(req.ParkingId)
            ?? throw new InvalidOperationException("Parking not found");

        var slot = await db.ParkingSlots.FindAsync(req.SlotId)
            ?? throw new InvalidOperationException("Slot not found");

        if (slot.Status != "available")
            throw new InvalidOperationException("Slot is not available");

        if (req.DurationHours <= 0) throw new InvalidOperationException("Duration must be greater than 0");

        var startUtc = req.StartTime.ToUniversalTime();
        var endUtc = startUtc.AddHours(req.DurationHours);
        var hours = req.DurationHours;

        var (amount, fees, total) = CalculatePrice(parking.RatePerHour, hours);

        var booking = new Booking
        {
            UserId = userId,
            ParkingId = req.ParkingId,
            SlotId = req.SlotId,
            VehiclePlate = req.VehiclePlate.ToUpper(),
            StartTime = startUtc,
            EndTime = endUtc,
            Status = "confirmed",
            TotalHours = Math.Round(hours, 2),
            Amount = amount,
            Fees = fees,
            TotalAmount = total,
            Currency = parking.Currency,
            PaymentStatus = "completed",
            PaymentMethod = req.PaymentMethod
        };

        slot.Status = "reserved";
        parking.AvailableSlots = Math.Max(0, parking.AvailableSlots - 1);
        parking.OccupiedSlots++;
        parking.IsFull = parking.AvailableSlots <= 0;

        db.Bookings.Add(booking);
        await db.SaveChangesAsync();
        return await MapAsync(booking.Id) ?? throw new Exception("Booking mapping failed");
    }

    public async Task<List<BookingResponse>> GetUserBookingsAsync(Guid userId)
    {
        var ids = await db.Bookings.Where(b => b.UserId == userId)
            .OrderByDescending(b => b.CreatedAt)
            .Select(b => b.Id)
            .ToListAsync();
        var result = new List<BookingResponse>();
        foreach (var id in ids)
        {
            var r = await MapAsync(id);
            if (r != null) result.Add(r);
        }
        return result;
    }

    public async Task<ActiveBookingResponse?> GetActiveAsync(Guid userId)
    {
        var booking = await db.Bookings
            .Include(b => b.Parking)
            .Include(b => b.Slot)
            .FirstOrDefaultAsync(b => b.UserId == userId && (b.Status == "confirmed" || b.Status == "active"));
        if (booking == null) return null;

        var remaining = (int)(booking.EndTime - DateTime.UtcNow).TotalSeconds;
        return new ActiveBookingResponse
        {
            Id = booking.Id,
            ParkingName = booking.Parking.Name,
            ParkingAddress = booking.Parking.Address,
            SlotId = booking.SlotId,
            SlotNumber = booking.Slot.SlotNumber,
            Floor = booking.Slot.Floor,
            RemainingTimeSeconds = Math.Max(0, remaining),
            StartTime = booking.StartTime,
            EndTime = booking.EndTime
        };
    }

    public async Task<List<BookingResponse>> GetHistoryAsync(Guid userId)
    {
        var ids = await db.Bookings
            .Where(b => b.UserId == userId && (b.Status == "completed" || b.Status == "cancelled"))
            .OrderByDescending(b => b.CreatedAt)
            .Select(b => b.Id)
            .ToListAsync();
        var result = new List<BookingResponse>();
        foreach (var id in ids)
        {
            var r = await MapAsync(id);
            if (r != null) result.Add(r);
        }
        return result;
    }

    public async Task<BookingResponse?> GetByIdAsync(Guid bookingId) => await MapAsync(bookingId);

    public async Task<BookingQRResponse?> GetQrAsync(Guid bookingId, Guid userId)
    {
        var b = await db.Bookings
            .Include(x => x.Parking)
            .Include(x => x.Slot)
            .FirstOrDefaultAsync(x => x.Id == bookingId && x.UserId == userId);
        if (b == null) return null;

        var qrData = System.Text.Json.JsonSerializer.Serialize(new
        {
            booking_id = b.Id,
            parking_id = b.ParkingId,
            slot_id = b.SlotId,
            vehicle_plate = b.VehiclePlate
        });

        return new BookingQRResponse
        {
            BookingId = b.Id,
            QrData = Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(qrData)),
            ParkingName = b.Parking.Name,
            SlotNumber = b.Slot.SlotNumber,
            StartTime = b.StartTime.ToString("o"),
            EndTime = b.EndTime.ToString("o"),
            VehiclePlate = b.VehiclePlate
        };
    }

    public async Task<BookingResponse> CancelAsync(Guid bookingId, Guid userId)
    {
        var booking = await db.Bookings
            .Include(b => b.Slot)
            .Include(b => b.Parking)
            .FirstOrDefaultAsync(b => b.Id == bookingId && b.UserId == userId)
            ?? throw new InvalidOperationException("Booking not found");

        if (booking.Status == "active")
            throw new InvalidOperationException("Cannot cancel an active booking. Check out first.");
        if (booking.Status is "completed" or "cancelled")
            throw new InvalidOperationException($"Booking is already {booking.Status}");

        booking.Status = "cancelled";
        booking.Slot.Status = "available";
        booking.Parking.AvailableSlots = Math.Min(booking.Parking.TotalSlots, booking.Parking.AvailableSlots + 1);
        booking.Parking.OccupiedSlots = Math.Max(0, booking.Parking.OccupiedSlots - 1);
        booking.Parking.IsFull = false;

        await db.SaveChangesAsync();
        return await MapAsync(bookingId) ?? throw new Exception("Mapping failed");
    }

    public async Task<BookingResponse?> CheckInAsync(Guid bookingId)
    {
        var booking = await db.Bookings
            .Include(b => b.Slot)
            .FirstOrDefaultAsync(b => b.Id == bookingId);
        if (booking == null || booking.Status != "confirmed") return null;

        booking.Status = "active";
        booking.Slot.Status = "occupied";
        booking.Slot.CurrentVehiclePlate = booking.VehiclePlate;
        await db.SaveChangesAsync();
        return await MapAsync(bookingId);
    }

    public async Task<BookingResponse?> CheckOutAsync(Guid bookingId)
    {
        var booking = await db.Bookings
            .Include(b => b.Slot)
            .Include(b => b.Parking)
            .FirstOrDefaultAsync(b => b.Id == bookingId);
        if (booking == null || booking.Status != "active") return null;

        var now = DateTime.UtcNow;
        booking.ActualExitTime = now;
        booking.Status = "completed";
        booking.Slot.Status = "available";
        booking.Slot.CurrentVehiclePlate = null;
        booking.Parking.AvailableSlots = Math.Min(booking.Parking.TotalSlots, booking.Parking.AvailableSlots + 1);
        booking.Parking.OccupiedSlots = Math.Max(0, booking.Parking.OccupiedSlots - 1);
        booking.Parking.IsFull = false;

        // Recalculate for overstay
        var actualHours = (now - booking.StartTime).TotalHours;
        if (actualHours > booking.TotalHours)
        {
            var parking = booking.Parking;
            var (amount, fees, total) = CalculatePrice(parking.RatePerHour, actualHours);
            booking.TotalHours = Math.Round(actualHours, 2);
            booking.Amount = amount;
            booking.Fees = fees;
            booking.TotalAmount = total;
        }

        await db.SaveChangesAsync();
        return await MapAsync(bookingId);
    }

    public async Task<BookingResponse> ExtendAsync(Guid bookingId, Guid userId, double additionalHours)
    {
        var booking = await db.Bookings
            .Include(b => b.Parking)
            .FirstOrDefaultAsync(b => b.Id == bookingId && b.UserId == userId)
            ?? throw new InvalidOperationException("Booking not found");

        if (booking.Status != "active" && booking.Status != "confirmed")
            throw new InvalidOperationException("Can only extend active or confirmed bookings");

        booking.EndTime = booking.EndTime.AddHours(additionalHours);
        var (amount, fees, total) = CalculatePrice(booking.Parking.RatePerHour, (booking.EndTime - booking.StartTime).TotalHours);
        booking.TotalHours = Math.Round((booking.EndTime - booking.StartTime).TotalHours, 2);
        booking.Amount = amount;
        booking.Fees = fees;
        booking.TotalAmount = total;

        await db.SaveChangesAsync();
        return await MapAsync(bookingId) ?? throw new Exception("Mapping failed");
    }

    public async Task<Booking?> FindByPlateAsync(Guid parkingId, string plate, IEnumerable<string> statuses)
    {
        var statusList = statuses.ToList();
        return await db.Bookings.FirstOrDefaultAsync(b =>
            b.ParkingId == parkingId &&
            b.VehiclePlate == plate.ToUpper() &&
            statusList.Contains(b.Status));
    }

    public async Task<List<BookingResponse>> GetAllAsync(string? status = null)
    {
        var q = db.Bookings.AsQueryable();
        if (!string.IsNullOrEmpty(status)) q = q.Where(b => b.Status == status);
        var ids = await q.OrderByDescending(b => b.CreatedAt).Select(b => b.Id).ToListAsync();
        var result = new List<BookingResponse>();
        foreach (var id in ids)
        {
            var r = await MapAsync(id);
            if (r != null) result.Add(r);
        }
        return result;
    }

    private async Task<BookingResponse?> MapAsync(Guid id)
    {
        var b = await db.Bookings
            .Include(x => x.Parking)
            .Include(x => x.Slot)
            .FirstOrDefaultAsync(x => x.Id == id);
        if (b == null) return null;
        return new BookingResponse
        {
            Id = b.Id,
            UserId = b.UserId,
            ParkingId = b.ParkingId,
            ParkingName = b.Parking.Name,
            ParkingAddress = b.Parking.Address,
            SlotId = b.SlotId,
            SlotNumber = b.Slot.SlotNumber,
            Floor = b.Slot.Floor,
            Section = b.Slot.Section,
            VehiclePlate = b.VehiclePlate,
            StartTime = b.StartTime,
            EndTime = b.EndTime,
            ActualExitTime = b.ActualExitTime,
            Status = b.Status,
            TotalHours = b.TotalHours,
            Amount = b.Amount,
            Fees = b.Fees,
            TotalAmount = b.TotalAmount,
            Currency = b.Currency,
            PaymentStatus = b.PaymentStatus,
            PaymentMethod = b.PaymentMethod,
            CreatedAt = b.CreatedAt
        };
    }

    private static (double amount, double fees, double total) CalculatePrice(double ratePerHour, double hours)
    {
        var amount = Math.Round(ratePerHour * hours, 2);
        var fees = Math.Round(amount * 0.05, 2);
        return (amount, fees, amount + fees);
    }
}
