using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Parkify.API.DTOs;
using Parkify.API.Services;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/bookings")]
[Authorize]
public class BookingsController(BookingService bookingService) : ControllerBase
{
    private Guid UserId => Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] BookingCreateRequest req)
    {
        try
        {
            return Ok(await bookingService.CreateAsync(UserId, req));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { detail = ex.Message });
        }
    }

    [HttpGet]
    public async Task<IActionResult> GetAll() => Ok(await bookingService.GetUserBookingsAsync(UserId));

    [HttpGet("active")]
    public async Task<IActionResult> GetActive() => Ok(await bookingService.GetActiveAsync(UserId));

    [HttpGet("history")]
    public async Task<IActionResult> GetHistory() => Ok(await bookingService.GetHistoryAsync(UserId));

    [HttpGet("{bookingId}")]
    public async Task<IActionResult> GetById(Guid bookingId)
    {
        var booking = await bookingService.GetByIdAsync(bookingId);
        if (booking == null || booking.UserId != UserId)
            return NotFound(new { detail = "Booking not found" });
        return Ok(booking);
    }

    [HttpGet("{bookingId}/qr")]
    public async Task<IActionResult> GetQr(Guid bookingId)
    {
        var qr = await bookingService.GetQrAsync(bookingId, UserId);
        if (qr == null) return NotFound(new { detail = "Booking not found" });
        return Ok(qr);
    }

    [HttpPost("{bookingId}/cancel")]
    public async Task<IActionResult> Cancel(Guid bookingId)
    {
        try
        {
            return Ok(await bookingService.CancelAsync(bookingId, UserId));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { detail = ex.Message });
        }
    }

    [HttpPost("{bookingId}/check-in")]
    public async Task<IActionResult> CheckIn(Guid bookingId)
    {
        var booking = await bookingService.GetByIdAsync(bookingId);
        if (booking == null || booking.UserId != UserId)
            return NotFound(new { detail = "Booking not found" });

        var result = await bookingService.CheckInAsync(bookingId);
        if (result == null)
            return BadRequest(new { detail = "Cannot check in - booking is not in confirmed status" });
        return Ok(result);
    }

    [HttpPost("{bookingId}/check-out")]
    public async Task<IActionResult> CheckOut(Guid bookingId)
    {
        var booking = await bookingService.GetByIdAsync(bookingId);
        if (booking == null || booking.UserId != UserId)
            return NotFound(new { detail = "Booking not found" });

        var result = await bookingService.CheckOutAsync(bookingId);
        if (result == null)
            return BadRequest(new { detail = "Cannot check out - booking is not in active status" });
        return Ok(result);
    }

    [HttpPost("{bookingId}/extend")]
    public async Task<IActionResult> Extend(Guid bookingId, [FromBody] BookingExtendRequest req)
    {
        try
        {
            return Ok(await bookingService.ExtendAsync(bookingId, UserId, req.AdditionalHours));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { detail = ex.Message });
        }
    }
}
