using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Parkify.API.Services;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/favorites")]
[Authorize]
public class FavoritesController(FavoriteService favoriteService) : ControllerBase
{
    private Guid UserId => Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    [HttpGet]
    public async Task<IActionResult> GetAll() => Ok(await favoriteService.GetUserFavoritesAsync(UserId));

    [HttpPost("{parkingId}")]
    public async Task<IActionResult> Add(Guid parkingId)
    {
        var fav = await favoriteService.AddAsync(UserId, parkingId);
        if (fav == null) return NotFound(new { detail = "Parking not found" });
        return Ok(fav);
    }

    [HttpDelete("{parkingId}")]
    public async Task<IActionResult> Remove(Guid parkingId)
    {
        if (!await favoriteService.RemoveAsync(UserId, parkingId))
            return NotFound(new { detail = "Favorite not found" });
        return Ok(new { success = true, message = "Removed from favorites" });
    }

    [HttpGet("{parkingId}/check")]
    public async Task<IActionResult> Check(Guid parkingId)
    {
        var isFav = await favoriteService.IsFavoritedAsync(UserId, parkingId);
        return Ok(new { is_favorited = isFav });
    }
}
