using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;
using Parkify.API.Services;
using Microsoft.EntityFrameworkCore;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/parkings")]
[Authorize]
public class ParkingsController(ParkingService parkingService, AppDbContext db) : ControllerBase
{
    private Guid UserId => Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    [HttpGet]
    public async Task<IActionResult> GetAll() => Ok(await parkingService.GetAllAsync(UserId));

    [HttpGet("search")]
    public async Task<IActionResult> SearchNearby(
        [FromQuery] double latitude,
        [FromQuery] double longitude,
        [FromQuery(Name = "radius_km")] double radiusKm = 10,
        [FromQuery(Name = "sort_by")] string sortBy = "distance")
    {
        return Ok(await parkingService.SearchNearbyAsync(latitude, longitude, radiusKm, sortBy, UserId));
    }

    [HttpGet("search-by-name")]
    public async Task<IActionResult> SearchByName([FromQuery] string q)
    {
        if (string.IsNullOrWhiteSpace(q))
            return BadRequest(new { detail = "Query must not be empty" });
        return Ok(await parkingService.SearchByNameAsync(q, UserId));
    }

    [HttpPost("filter")]
    public async Task<IActionResult> FilterPost([FromBody] ParkingFilterBody req)
    {
        return Ok(await parkingService.FilterAsync(
            req.Latitude, req.Longitude, req.RadiusKm,
            req.MinPrice, req.MaxPrice, req.ParkingType,
            req.SortBy, req.Amenities, req.AvailableOnly, UserId));
    }

    [HttpGet("filter")]
    public async Task<IActionResult> FilterGet(
        [FromQuery] double? latitude,
        [FromQuery] double? longitude,
        [FromQuery(Name = "radius_km")] double radiusKm = 10,
        [FromQuery(Name = "min_price")] double? minPrice = null,
        [FromQuery(Name = "max_price")] double? maxPrice = null,
        [FromQuery(Name = "parking_type")] string? parkingType = null,
        [FromQuery(Name = "sort_by")] string sortBy = "distance",
        [FromQuery(Name = "available_only")] bool availableOnly = true)
    {
        return Ok(await parkingService.FilterAsync(
            latitude, longitude, radiusKm,
            minPrice, maxPrice, parkingType,
            sortBy, null, availableOnly, UserId));
    }

    [HttpGet("{parkingId}")]
    public async Task<IActionResult> GetById(Guid parkingId)
    {
        var p = await parkingService.GetByIdAsync(parkingId, UserId);
        if (p == null) return NotFound(new { detail = "Parking not found" });
        return Ok(p);
    }

    [HttpGet("{parkingId}/slots")]
    public async Task<IActionResult> GetSlots(Guid parkingId)
    {
        var p = await parkingService.GetByIdAsync(parkingId);
        if (p == null) return NotFound(new { detail = "Parking not found" });
        return Ok(await parkingService.GetSlotsAsync(parkingId));
    }

    [HttpGet("{parkingId}/slots/available")]
    public async Task<IActionResult> GetAvailableSlots(Guid parkingId)
    {
        var p = await parkingService.GetByIdAsync(parkingId);
        if (p == null) return NotFound(new { detail = "Parking not found" });
        return Ok(await parkingService.GetSlotsAsync(parkingId, availableOnly: true));
    }

    [HttpPost("{parkingId}/watch")]
    public async Task<IActionResult> Watch(Guid parkingId)
    {
        var p = await parkingService.GetByIdAsync(parkingId);
        if (p == null) return NotFound(new { detail = "Parking not found" });

        var exists = await db.SpotWatchers.AnyAsync(w => w.ParkingId == parkingId && w.UserId == UserId);
        if (!exists)
        {
            db.SpotWatchers.Add(new SpotWatcher { ParkingId = parkingId, UserId = UserId });
            await db.SaveChangesAsync();
        }
        return Ok(new { success = true, message = "You will be notified when a spot becomes available" });
    }

    [HttpDelete("{parkingId}/watch")]
    public async Task<IActionResult> Unwatch(Guid parkingId)
    {
        var w = await db.SpotWatchers.FirstOrDefaultAsync(x => x.ParkingId == parkingId && x.UserId == UserId);
        if (w != null) { db.SpotWatchers.Remove(w); await db.SaveChangesAsync(); }
        return Ok(new { success = true, message = "Unsubscribed from availability notifications" });
    }

    [HttpGet("{parkingId}/watch")]
    public async Task<IActionResult> CheckWatch(Guid parkingId)
    {
        var p = await parkingService.GetByIdAsync(parkingId);
        if (p == null) return NotFound(new { detail = "Parking not found" });
        var isWatching = await db.SpotWatchers.AnyAsync(w => w.ParkingId == parkingId && w.UserId == UserId);
        return Ok(new { is_watching = isWatching });
    }
}

public record ParkingFilterBody(
    double? Latitude,
    double? Longitude,
    double RadiusKm = 10,
    double? MinPrice = null,
    double? MaxPrice = null,
    string? ParkingType = null,
    string SortBy = "distance",
    List<string>? Amenities = null,
    bool AvailableOnly = true
);
