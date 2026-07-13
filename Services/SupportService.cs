using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class SupportService(AppDbContext db)
{
    public async Task<SupportTicketResponse> CreateAsync(Guid userId, SupportTicketCreateRequest req)
    {
        var ticket = new SupportTicket
        {
            UserId = userId,
            Subject = req.Subject,
            Message = req.Message,
            Category = req.Category
        };
        db.SupportTickets.Add(ticket);
        await db.SaveChangesAsync();
        return Map(ticket);
    }

    public async Task<List<SupportTicketResponse>> GetUserTicketsAsync(Guid userId)
    {
        var tickets = await db.SupportTickets
            .Where(t => t.UserId == userId)
            .OrderByDescending(t => t.CreatedAt)
            .ToListAsync();
        return tickets.Select(Map).ToList();
    }

    public async Task<List<SupportTicketResponse>> GetAllAsync()
    {
        var tickets = await db.SupportTickets.OrderByDescending(t => t.CreatedAt).ToListAsync();
        return tickets.Select(Map).ToList();
    }

    public async Task<SupportTicketResponse?> UpdateStatusAsync(Guid ticketId, string status)
    {
        var ticket = await db.SupportTickets.FindAsync(ticketId);
        if (ticket == null) return null;
        ticket.Status = status;
        ticket.UpdatedAt = DateTime.UtcNow;
        await db.SaveChangesAsync();
        return Map(ticket);
    }

    private static SupportTicketResponse Map(SupportTicket t) => new()
    {
        Id = t.Id,
        UserId = t.UserId,
        Subject = t.Subject,
        Message = t.Message,
        Category = t.Category,
        Status = t.Status,
        CreatedAt = t.CreatedAt.ToString("o"),
        UpdatedAt = t.UpdatedAt?.ToString("o")
    };
}
