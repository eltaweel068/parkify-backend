using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Parkify.API.DTOs;
using Parkify.API.Services;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/support")]
[Authorize]
public class SupportController(SupportService supportService) : ControllerBase
{
    private Guid UserId => Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    [HttpPost("tickets")]
    public async Task<IActionResult> Create([FromBody] SupportTicketCreateRequest req) =>
        Ok(await supportService.CreateAsync(UserId, req));

    [HttpGet("tickets")]
    public async Task<IActionResult> GetAll() => Ok(await supportService.GetUserTicketsAsync(UserId));

    [HttpGet("tickets/{ticketId}")]
    public async Task<IActionResult> GetById(Guid ticketId)
    {
        var tickets = await supportService.GetUserTicketsAsync(UserId);
        var ticket = tickets.FirstOrDefault(t => t.Id == ticketId);
        if (ticket == null) return NotFound(new { detail = "Ticket not found" });
        return Ok(ticket);
    }
}
