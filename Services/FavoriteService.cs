using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class FavoriteService(AppDbContext db, ParkingService parkingService)
{
    public async Task<List<FavoriteResponse>> GetUserFavoritesAsync(Guid userId)
    {
        var favs = await db.Favorites
            .Where(f => f.UserId == userId)
            .OrderByDescending(f => f.CreatedAt)
            .ToListAsync();

        var result = new List<FavoriteResponse>();
        foreach (var fav in favs)
        {
            var parking = await parkingService.GetByIdAsync(fav.ParkingId, userId);
            if (parking == null) continue;
            result.Add(new FavoriteResponse
            {
                Id = fav.Id,
                UserId = fav.UserId,
                ParkingId = fav.ParkingId,
                Parking = parking,
                CreatedAt = fav.CreatedAt.ToString("o")
            });
        }
        return result;
    }

    public async Task<FavoriteResponse?> AddAsync(Guid userId, Guid parkingId)
    {
        var parking = await db.Parkings.FindAsync(parkingId);
        if (parking == null) return null;

        var existing = await db.Favorites.FirstOrDefaultAsync(f => f.UserId == userId && f.ParkingId == parkingId);
        if (existing != null)
        {
            var parkingDto = await parkingService.GetByIdAsync(parkingId, userId);
            return new FavoriteResponse
            {
                Id = existing.Id,
                UserId = existing.UserId,
                ParkingId = existing.ParkingId,
                Parking = parkingDto!,
                CreatedAt = existing.CreatedAt.ToString("o")
            };
        }

        var fav = new Favorite { UserId = userId, ParkingId = parkingId };
        db.Favorites.Add(fav);
        await db.SaveChangesAsync();

        var p = await parkingService.GetByIdAsync(parkingId, userId);
        return new FavoriteResponse
        {
            Id = fav.Id,
            UserId = fav.UserId,
            ParkingId = fav.ParkingId,
            Parking = p!,
            CreatedAt = fav.CreatedAt.ToString("o")
        };
    }

    public async Task<bool> RemoveAsync(Guid userId, Guid parkingId)
    {
        var fav = await db.Favorites.FirstOrDefaultAsync(f => f.UserId == userId && f.ParkingId == parkingId);
        if (fav == null) return false;
        db.Favorites.Remove(fav);
        await db.SaveChangesAsync();
        return true;
    }

    public async Task<bool> IsFavoritedAsync(Guid userId, Guid parkingId) =>
        await db.Favorites.AnyAsync(f => f.UserId == userId && f.ParkingId == parkingId);
}
