using Microsoft.EntityFrameworkCore;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;

namespace Parkify.API.Services;

public class UserService(AppDbContext db)
{
    // ─── Cars ────────────────────────────────────────────────

    public async Task<List<CarResponse>> GetCarsAsync(Guid userId)
    {
        var cars = await db.Cars.Where(c => c.UserId == userId).OrderByDescending(c => c.CreatedAt).ToListAsync();
        return cars.Select(MapCar).ToList();
    }

    public async Task<CarResponse?> AddCarAsync(Guid userId, CarCreateRequest req)
    {
        var user = await db.Users.FindAsync(userId);
        if (user == null) return null;

        if (req.IsDefault)
            await ClearDefaultCarsAsync(userId);

        var car = new Car
        {
            UserId = userId,
            LicensePlate = req.Plate.ToUpper(),
            Make = req.Make,
            Model = req.Model,
            Year = req.Year,
            Color = req.Color,
            IsDefault = req.IsDefault
        };
        db.Cars.Add(car);
        await db.SaveChangesAsync();
        return MapCar(car);
    }

    public async Task<CarResponse?> UpdateCarAsync(Guid userId, Guid carId, CarUpdateRequest req)
    {
        var car = await db.Cars.FirstOrDefaultAsync(c => c.Id == carId && c.UserId == userId);
        if (car == null) return null;
        if (req.Plate != null) car.LicensePlate = req.Plate.ToUpper();
        if (req.Make != null) car.Make = req.Make;
        if (req.Model != null) car.Model = req.Model;
        if (req.Year.HasValue) car.Year = req.Year;
        if (req.Color != null) car.Color = req.Color;
        await db.SaveChangesAsync();
        return MapCar(car);
    }

    public async Task<bool> DeleteCarAsync(Guid userId, Guid carId)
    {
        var car = await db.Cars.FirstOrDefaultAsync(c => c.Id == carId && c.UserId == userId);
        if (car == null) return false;
        db.Cars.Remove(car);
        await db.SaveChangesAsync();
        return true;
    }

    public async Task<CarResponse?> SetDefaultCarAsync(Guid userId, Guid carId)
    {
        var car = await db.Cars.FirstOrDefaultAsync(c => c.Id == carId && c.UserId == userId);
        if (car == null) return null;
        await ClearDefaultCarsAsync(userId);
        car.IsDefault = true;
        await db.SaveChangesAsync();
        return MapCar(car);
    }

    // ─── Payment Methods ─────────────────────────────────────

    public async Task<List<PaymentMethodResponse>> GetPaymentMethodsAsync(Guid userId)
    {
        var methods = await db.PaymentMethods.Where(m => m.UserId == userId).OrderByDescending(m => m.CreatedAt).ToListAsync();
        return methods.Select(MapPm).ToList();
    }

    public async Task<PaymentMethodResponse?> AddPaymentMethodAsync(Guid userId, PaymentMethodCreateRequest req)
    {
        var user = await db.Users.FindAsync(userId);
        if (user == null) return null;

        if (req.IsDefault)
            await ClearDefaultPaymentMethodsAsync(userId);

        string? lastFour = null;
        string? expiry = null;
        if (req.CardNumber != null && req.CardNumber.Length >= 4)
            lastFour = req.CardNumber[^4..];
        if (req.ExpiryMonth.HasValue && req.ExpiryYear.HasValue)
            expiry = $"{req.ExpiryMonth:D2}/{req.ExpiryYear % 100:D2}";

        var pm = new PaymentMethod
        {
            UserId = userId,
            MethodType = req.CardType,
            LastFour = lastFour,
            CardHolder = req.CardHolderName,
            Expiry = expiry,
            IsDefault = req.IsDefault
        };
        db.PaymentMethods.Add(pm);
        await db.SaveChangesAsync();
        return MapPm(pm);
    }

    public async Task<bool> DeletePaymentMethodAsync(Guid userId, Guid methodId)
    {
        var pm = await db.PaymentMethods.FirstOrDefaultAsync(m => m.Id == methodId && m.UserId == userId);
        if (pm == null) return false;
        db.PaymentMethods.Remove(pm);
        await db.SaveChangesAsync();
        return true;
    }

    public async Task<PaymentMethodResponse?> SetDefaultPaymentMethodAsync(Guid userId, Guid methodId)
    {
        var pm = await db.PaymentMethods.FirstOrDefaultAsync(m => m.Id == methodId && m.UserId == userId);
        if (pm == null) return null;
        await ClearDefaultPaymentMethodsAsync(userId);
        pm.IsDefault = true;
        await db.SaveChangesAsync();
        return MapPm(pm);
    }

    private async Task ClearDefaultCarsAsync(Guid userId)
    {
        var defaults = await db.Cars.Where(c => c.UserId == userId && c.IsDefault).ToListAsync();
        foreach (var c in defaults) c.IsDefault = false;
    }

    private async Task ClearDefaultPaymentMethodsAsync(Guid userId)
    {
        var defaults = await db.PaymentMethods.Where(m => m.UserId == userId && m.IsDefault).ToListAsync();
        foreach (var m in defaults) m.IsDefault = false;
    }

    private static CarResponse MapCar(Car c) => new()
    {
        Id = c.Id,
        Plate = c.LicensePlate,
        Make = c.Make,
        Model = c.Model,
        Year = c.Year,
        Color = c.Color,
        IsDefault = c.IsDefault
    };

    private static PaymentMethodResponse MapPm(PaymentMethod m) => new()
    {
        Id = m.Id,
        CardType = m.MethodType,
        LastFour = m.LastFour,
        CardHolderName = m.CardHolder,
        Expiry = m.Expiry,
        IsDefault = m.IsDefault
    };
}
