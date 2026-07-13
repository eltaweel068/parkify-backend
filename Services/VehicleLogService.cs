using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class VehicleLogService(AppDbContext db)
{
    public async Task<VehicleLog> AddLogAsync(Guid parkingId, string plate, string action, string? gate, double? confidence = null, string? plateImage = null)
    {
        var log = new VehicleLog
        {
            ParkingId = parkingId,
            VehiclePlate = plate.ToUpper(),
            Action = action,
            Gate = gate,
            Confidence = confidence,
            PlateImage = plateImage,
            Timestamp = DateTime.UtcNow
        };
        db.VehicleLogs.Add(log);
        await db.SaveChangesAsync();
        return log;
    }

    public async Task<List<VehicleLogResponse>> GetLogsAsync(Guid? parkingId, string? action, int limit = 50)
    {
        var q = db.VehicleLogs.Include(l => l.Parking).AsQueryable();
        if (parkingId.HasValue) q = q.Where(l => l.ParkingId == parkingId);
        if (!string.IsNullOrEmpty(action)) q = q.Where(l => l.Action == action);
        var logs = await q.OrderByDescending(l => l.Timestamp).Take(limit).ToListAsync();
        return logs.Select(l => new VehicleLogResponse
        {
            Id = l.Id,
            ParkingId = l.ParkingId,
            ParkingName = l.Parking.Name,
            VehiclePlate = l.VehiclePlate,
            Action = l.Action,
            Gate = l.Gate ?? string.Empty,
            Timestamp = l.Timestamp.ToString("o"),
            PlateImage = l.PlateImage,
            Confidence = l.Confidence
        }).ToList();
    }
}
