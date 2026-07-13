using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class ParkingService(AppDbContext db)
{
    public async Task<List<ParkingResponse>> GetAllAsync(Guid? userId = null)
    {
        var parkings = await db.Parkings.Where(p => p.IsActive).ToListAsync();
        return await MapListAsync(parkings, userId);
    }

    public async Task<ParkingResponse?> GetByIdAsync(Guid id, Guid? userId = null)
    {
        var parking = await db.Parkings.FindAsync(id);
        if (parking == null) return null;
        return await MapAsync(parking, userId);
    }

    public async Task<List<ParkingResponse>> SearchNearbyAsync(double lat, double lon, double radiusKm, string sortBy, Guid? userId = null)
    {
        var parkings = await db.Parkings.Where(p => p.IsActive).ToListAsync();
        var result = parkings
            .Select(p => (parking: p, dist: Haversine(lat, lon, p.Latitude, p.Longitude)))
            .Where(x => x.dist <= radiusKm * 1000)
            .OrderBy(x => sortBy == "price" ? x.parking.RatePerHour : sortBy == "rating" ? -x.parking.Rating : x.dist)
            .Select(x => x.parking)
            .ToList();

        return await MapListAsync(result, userId, lat, lon);
    }

    public async Task<List<ParkingResponse>> SearchByNameAsync(string q, Guid? userId = null)
    {
        var lower = q.ToLower();
        var parkings = await db.Parkings
            .Where(p => p.IsActive && (
                p.Name.ToLower().Contains(lower) ||
                p.Address.ToLower().Contains(lower) ||
                (p.City != null && p.City.ToLower().Contains(lower)) ||
                (p.Description != null && p.Description.ToLower().Contains(lower))))
            .ToListAsync();
        return await MapListAsync(parkings, userId);
    }

    public async Task<List<ParkingResponse>> FilterAsync(
        double? lat, double? lon, double radiusKm,
        double? minPrice, double? maxPrice,
        string? parkingType, string sortBy,
        List<string>? amenities, bool availableOnly,
        Guid? userId = null)
    {
        var query = db.Parkings.Where(p => p.IsActive);
        if (minPrice.HasValue) query = query.Where(p => p.RatePerHour >= minPrice);
        if (maxPrice.HasValue) query = query.Where(p => p.RatePerHour <= maxPrice);
        if (!string.IsNullOrEmpty(parkingType)) query = query.Where(p => p.ParkingType == parkingType);
        if (availableOnly) query = query.Where(p => p.AvailableSlots > 0);

        var parkings = await query.ToListAsync();

        if (amenities != null && amenities.Count > 0)
            parkings = parkings.Where(p => amenities.All(a => p.Amenities.Contains(a))).ToList();

        if (lat.HasValue && lon.HasValue)
        {
            parkings = parkings
                .Select(p => (p, dist: Haversine(lat.Value, lon.Value, p.Latitude, p.Longitude)))
                .Where(x => x.dist <= radiusKm * 1000)
                .OrderBy(x => sortBy == "price" ? x.p.RatePerHour : sortBy == "rating" ? -x.p.Rating : x.dist)
                .Select(x => x.p)
                .ToList();
            return await MapListAsync(parkings, userId, lat.Value, lon.Value);
        }

        return await MapListAsync(parkings, userId);
    }

    public async Task<List<ParkingSlotResponse>> GetSlotsAsync(Guid parkingId, bool availableOnly = false)
    {
        var q = db.ParkingSlots.Where(s => s.ParkingId == parkingId);
        if (availableOnly) q = q.Where(s => s.Status == "available");
        var slots = await q.OrderBy(s => s.Floor).ThenBy(s => s.SlotNumber).ToListAsync();
        return slots.Select(MapSlot).ToList();
    }

    public async Task<ParkingSlot?> GetSlotByIdAsync(Guid slotId) =>
        await db.ParkingSlots.FindAsync(slotId);

    public async Task<ParkingResponse> CreateAsync(ParkingCreateRequest req)
    {
        var parking = new Parking
        {
            Name = req.Name,
            Description = req.Description,
            Latitude = req.Latitude,
            Longitude = req.Longitude,
            Address = req.Address,
            City = req.City,
            Country = req.Country,
            ParkingType = req.ParkingType,
            TotalSlots = req.TotalSlots,
            AvailableSlots = req.TotalSlots,
            RatePerHour = req.RatePerHour,
            Currency = req.Currency,
            Amenities = req.Amenities,
            Is247 = req.Is247,
            DeviceKey = req.DeviceKey
        };
        db.Parkings.Add(parking);

        for (int i = 1; i <= req.TotalSlots; i++)
        {
            db.ParkingSlots.Add(new ParkingSlot
            {
                ParkingId = parking.Id,
                SlotNumber = i.ToString("D2"),
                Floor = 1,
                Status = "available"
            });
        }

        await db.SaveChangesAsync();
        return await MapAsync(parking) ?? throw new Exception("Failed to create parking");
    }

    public async Task<ParkingResponse?> UpdateAsync(Guid id, ParkingUpdateRequest req)
    {
        var parking = await db.Parkings.FindAsync(id);
        if (parking == null) return null;

        if (req.Name != null) parking.Name = req.Name;
        if (req.Description != null) parking.Description = req.Description;
        if (req.Latitude.HasValue) parking.Latitude = req.Latitude.Value;
        if (req.Longitude.HasValue) parking.Longitude = req.Longitude.Value;
        if (req.Address != null) parking.Address = req.Address;
        if (req.City != null) parking.City = req.City;
        if (req.ParkingType != null) parking.ParkingType = req.ParkingType;
        if (req.RatePerHour.HasValue) parking.RatePerHour = req.RatePerHour.Value;
        if (req.Amenities != null) parking.Amenities = req.Amenities;
        if (req.Is247.HasValue) parking.Is247 = req.Is247.Value;
        if (req.IsActive.HasValue) parking.IsActive = req.IsActive.Value;
        if (req.DeviceKey != null) parking.DeviceKey = req.DeviceKey;

        await db.SaveChangesAsync();
        return await MapAsync(parking);
    }

    public async Task<bool> DeleteAsync(Guid id)
    {
        var parking = await db.Parkings.FindAsync(id);
        if (parking == null) return false;
        parking.IsActive = false;
        await db.SaveChangesAsync();
        return true;
    }

    public async Task SyncCapacityAsync(Guid parkingId)
    {
        var parking = await db.Parkings.FindAsync(parkingId);
        if (parking == null) return;
        var occupied = await db.ParkingSlots.CountAsync(s => s.ParkingId == parkingId && s.Status == "occupied");
        parking.OccupiedSlots = occupied;
        parking.AvailableSlots = parking.TotalSlots - occupied;
        parking.IsFull = parking.AvailableSlots <= 0;
        await db.SaveChangesAsync();
    }

    public async Task<bool> ValidateDeviceKeyAsync(Guid parkingId, string deviceKey)
    {
        var parking = await db.Parkings.FindAsync(parkingId);
        return parking?.DeviceKey == deviceKey;
    }

    private async Task<List<ParkingResponse>> MapListAsync(List<Parking> parkings, Guid? userId = null, double? lat = null, double? lon = null)
    {
        var favSet = userId.HasValue
            ? (await db.Favorites.Where(f => f.UserId == userId).Select(f => f.ParkingId).ToListAsync()).ToHashSet()
            : new HashSet<Guid>();

        return parkings.Select(p =>
        {
            double? dist = lat.HasValue && lon.HasValue ? Haversine(lat.Value, lon.Value, p.Latitude, p.Longitude) : null;
            return MapParking(p, dist, userId.HasValue ? favSet.Contains(p.Id) : null);
        }).ToList();
    }

    private async Task<ParkingResponse?> MapAsync(Parking p, Guid? userId = null, double? lat = null, double? lon = null)
    {
        bool? isFav = null;
        if (userId.HasValue)
            isFav = await db.Favorites.AnyAsync(f => f.UserId == userId && f.ParkingId == p.Id);
        double? dist = lat.HasValue && lon.HasValue ? Haversine(lat.Value, lon.Value, p.Latitude, p.Longitude) : null;
        return MapParking(p, dist, isFav);
    }

    private static ParkingResponse MapParking(Parking p, double? distMeters, bool? isFavorited)
    {
        int? walkingMin = distMeters.HasValue ? (int)(distMeters.Value / 1.4 / 60) : null;
        return new ParkingResponse
        {
            Id = p.Id,
            Name = p.Name,
            Description = p.Description,
            Location = new LocationDto
            {
                Latitude = p.Latitude,
                Longitude = p.Longitude,
                Address = p.Address,
                City = p.City,
                Country = p.Country
            },
            ParkingType = p.ParkingType,
            TotalSlots = p.TotalSlots,
            AvailableSlots = p.AvailableSlots,
            OccupiedSlots = p.OccupiedSlots,
            IsFull = p.IsFull,
            RatePerHour = p.RatePerHour,
            Currency = p.Currency,
            Amenities = p.Amenities,
            Images = p.Images,
            Rating = p.Rating,
            ReviewCount = p.ReviewCount,
            Is247 = p.Is247,
            IsActive = p.IsActive,
            DistanceMeters = distMeters,
            WalkingTimeMinutes = walkingMin,
            IsFavorited = isFavorited
        };
    }

    private static ParkingSlotResponse MapSlot(ParkingSlot s) => new()
    {
        Id = s.Id,
        ParkingId = s.ParkingId,
        SlotNumber = s.SlotNumber,
        Floor = s.Floor,
        Section = s.Section,
        Status = s.Status,
        IsHandicap = s.IsHandicap,
        IsEvCharging = s.IsEvCharging,
        CurrentVehiclePlate = s.CurrentVehiclePlate
    };

    public static double Haversine(double lat1, double lon1, double lat2, double lon2)
    {
        const double R = 6371000;
        var phi1 = Math.PI * lat1 / 180;
        var phi2 = Math.PI * lat2 / 180;
        var dphi = Math.PI * (lat2 - lat1) / 180;
        var dlambda = Math.PI * (lon2 - lon1) / 180;
        var a = Math.Sin(dphi / 2) * Math.Sin(dphi / 2)
              + Math.Cos(phi1) * Math.Cos(phi2) * Math.Sin(dlambda / 2) * Math.Sin(dlambda / 2);
        return 2 * R * Math.Asin(Math.Sqrt(a));
    }
}
