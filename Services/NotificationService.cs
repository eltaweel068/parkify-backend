using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class NotificationService(AppDbContext db)
{
    public async Task<Notification> CreateAsync(Guid userId, string title, string message, string type, string? dataJson = null)
    {
        var notif = new Notification
        {
            UserId = userId,
            Title = title,
            Message = message,
            NotificationType = type,
            Data = dataJson
        };
        db.Notifications.Add(notif);
        await db.SaveChangesAsync();
        return notif;
    }

    public async Task<int> BroadcastAsync(string title, string message, string type)
    {
        var userIds = await db.Users.Where(u => u.IsActive).Select(u => u.Id).ToListAsync();
        foreach (var uid in userIds)
            db.Notifications.Add(new Notification { UserId = uid, Title = title, Message = message, NotificationType = type });
        await db.SaveChangesAsync();
        return userIds.Count;
    }

    public async Task<List<NotificationResponse>> GetUserNotificationsAsync(Guid userId)
    {
        var notifs = await db.Notifications
            .Where(n => n.UserId == userId)
            .OrderByDescending(n => n.CreatedAt)
            .ToListAsync();
        return notifs.Select(Map).ToList();
    }

    public async Task<int> GetUnreadCountAsync(Guid userId) =>
        await db.Notifications.CountAsync(n => n.UserId == userId && !n.IsRead);

    public async Task<NotificationResponse?> MarkReadAsync(Guid notifId, Guid userId)
    {
        var n = await db.Notifications.FirstOrDefaultAsync(x => x.Id == notifId && x.UserId == userId);
        if (n == null) return null;
        n.IsRead = true;
        await db.SaveChangesAsync();
        return Map(n);
    }

    public async Task<int> MarkAllReadAsync(Guid userId)
    {
        var unread = await db.Notifications.Where(n => n.UserId == userId && !n.IsRead).ToListAsync();
        foreach (var n in unread) n.IsRead = true;
        await db.SaveChangesAsync();
        return unread.Count;
    }

    public async Task<bool> DeleteAsync(Guid notifId, Guid userId)
    {
        var n = await db.Notifications.FirstOrDefaultAsync(x => x.Id == notifId && x.UserId == userId);
        if (n == null) return false;
        db.Notifications.Remove(n);
        await db.SaveChangesAsync();
        return true;
    }

    private static NotificationResponse Map(Notification n) => new()
    {
        Id = n.Id,
        UserId = n.UserId,
        Title = n.Title,
        Message = n.Message,
        NotificationType = n.NotificationType,
        IsRead = n.IsRead,
        Data = n.Data != null ? System.Text.Json.JsonSerializer.Deserialize<object>(n.Data) : null,
        CreatedAt = n.CreatedAt.ToString("o")
    };
}
