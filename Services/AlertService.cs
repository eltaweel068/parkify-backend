using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class AlertService(AppDbContext db)
{
    public async Task<AlertResponse> CreateAsync(Guid parkingId, string alertType, string severity, string message)
    {
        var parking = await db.Parkings.FindAsync(parkingId)
            ?? throw new InvalidOperationException("Parking not found");

        var alert = new Alert
        {
            ParkingId = parkingId,
            AlertType = alertType,
            Severity = severity,
            Message = message
        };
        db.Alerts.Add(alert);
        await db.SaveChangesAsync();
        return Map(alert, parking.Name);
    }

    public async Task<List<AlertResponse>> GetAllAsync(string? status = null)
    {
        var q = db.Alerts.Include(a => a.Parking).AsQueryable();
        if (!string.IsNullOrEmpty(status)) q = q.Where(a => a.Status == status);
        var alerts = await q.OrderByDescending(a => a.CreatedAt).ToListAsync();
        return alerts.Select(a => Map(a, a.Parking.Name)).ToList();
    }

    public async Task<AlertResponse?> GetByIdAsync(Guid id)
    {
        var a = await db.Alerts.Include(x => x.Parking).FirstOrDefaultAsync(x => x.Id == id);
        return a == null ? null : Map(a, a.Parking.Name);
    }

    public async Task<AlertResponse?> AcknowledgeAsync(Guid id)
    {
        var a = await db.Alerts.Include(x => x.Parking).FirstOrDefaultAsync(x => x.Id == id);
        if (a == null) return null;
        a.Status = "acknowledged";
        await db.SaveChangesAsync();
        return Map(a, a.Parking.Name);
    }

    public async Task<AlertResponse?> ResolveAsync(Guid id, Guid resolvedBy)
    {
        var a = await db.Alerts.Include(x => x.Parking).FirstOrDefaultAsync(x => x.Id == id);
        if (a == null) return null;
        a.Status = "resolved";
        a.ResolvedAt = DateTime.UtcNow;
        a.ResolvedBy = resolvedBy;
        await db.SaveChangesAsync();
        return Map(a, a.Parking.Name);
    }

    public async Task<int> GetActiveCountAsync() =>
        await db.Alerts.CountAsync(a => a.Status == "active");

    private static AlertResponse Map(Alert a, string parkingName) => new()
    {
        Id = a.Id,
        ParkingId = a.ParkingId,
        ParkingName = parkingName,
        AlertType = a.AlertType,
        Severity = a.Severity,
        Message = a.Message,
        Status = a.Status,
        CreatedAt = a.CreatedAt.ToString("o"),
        ResolvedAt = a.ResolvedAt?.ToString("o"),
        ResolvedBy = a.ResolvedBy?.ToString()
    };
}
