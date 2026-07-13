using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Parkify.API.DTOs;
using Parkify.API.Services;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/users")]
[Authorize]
public class UsersController(AuthService authService, UserService userService) : ControllerBase
{
    private Guid UserId => Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    // ─── Profile ──────────────────────────────────────────────

    [HttpGet("profile")]
    public async Task<IActionResult> GetProfile()
    {
        var user = await authService.GetByIdAsync(UserId);
        if (user == null) return NotFound(new { detail = "User not found" });
        return Ok(MapProfile(user));
    }

    [HttpPut("profile")]
    public async Task<IActionResult> UpdateProfile([FromBody] UpdateProfileRequest req)
    {
        if (req.Email != null)
        {
            var existing = await authService.GetByEmailAsync(req.Email);
            if (existing != null && existing.Id != UserId)
                return BadRequest(new { detail = "Email already in use" });
        }
        var user = await authService.UpdateProfileAsync(UserId, req);
        if (user == null) return NotFound(new { detail = "User not found" });
        return Ok(MapProfile(user));
    }

    [HttpPost("profile/complete")]
    public async Task<IActionResult> CompleteProfile([FromBody] CompleteProfileRequest req)
    {
        var user = await authService.CompleteProfileAsync(UserId, req);
        if (user == null) return NotFound(new { detail = "User not found" });
        return Ok(MapProfile(user));
    }

    [HttpPut("change-password")]
    public async Task<IActionResult> ChangePassword([FromBody] ChangePasswordRequest req)
    {
        try
        {
            await authService.ChangePasswordAsync(UserId, req.CurrentPassword, req.NewPassword);
            return Ok(new { success = true, message = "Password changed successfully" });
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { detail = ex.Message });
        }
    }

    // ─── Cars ─────────────────────────────────────────────────

    [HttpGet("cars")]
    public async Task<IActionResult> GetCars() => Ok(await userService.GetCarsAsync(UserId));

    [HttpPost("cars")]
    public async Task<IActionResult> AddCar([FromBody] CarCreateRequest req)
    {
        var car = await userService.AddCarAsync(UserId, req);
        if (car == null) return NotFound(new { detail = "User not found" });
        return Ok(car);
    }

    [HttpPut("cars/{carId}")]
    public async Task<IActionResult> UpdateCar(Guid carId, [FromBody] CarUpdateRequest req)
    {
        var car = await userService.UpdateCarAsync(UserId, carId, req);
        if (car == null) return NotFound(new { detail = "Car not found" });
        return Ok(car);
    }

    [HttpDelete("cars/{carId}")]
    public async Task<IActionResult> DeleteCar(Guid carId)
    {
        if (!await userService.DeleteCarAsync(UserId, carId))
            return NotFound(new { detail = "Car not found" });
        return Ok(new { success = true, message = "Car removed successfully" });
    }

    [HttpPut("cars/{carId}/default")]
    public async Task<IActionResult> SetDefaultCar(Guid carId)
    {
        var car = await userService.SetDefaultCarAsync(UserId, carId);
        if (car == null) return NotFound(new { detail = "Car not found" });
        return Ok(car);
    }

    // ─── Payment Methods ──────────────────────────────────────

    [HttpGet("payment-methods")]
    public async Task<IActionResult> GetPaymentMethods() => Ok(await userService.GetPaymentMethodsAsync(UserId));

    [HttpPost("payment-methods")]
    public async Task<IActionResult> AddPaymentMethod([FromBody] PaymentMethodCreateRequest req)
    {
        var pm = await userService.AddPaymentMethodAsync(UserId, req);
        if (pm == null) return NotFound(new { detail = "User not found" });
        return Ok(pm);
    }

    [HttpDelete("payment-methods/{methodId}")]
    public async Task<IActionResult> DeletePaymentMethod(Guid methodId)
    {
        if (!await userService.DeletePaymentMethodAsync(UserId, methodId))
            return NotFound(new { detail = "Payment method not found" });
        return Ok(new { success = true, message = "Payment method removed" });
    }

    [HttpPut("payment-methods/{methodId}/default")]
    public async Task<IActionResult> SetDefaultPayment(Guid methodId)
    {
        var pm = await userService.SetDefaultPaymentMethodAsync(UserId, methodId);
        if (pm == null) return NotFound(new { detail = "Payment method not found" });
        return Ok(pm);
    }

    private static UserProfileResponse MapProfile(Models.User u) => new()
    {
        Id = u.Id,
        Email = u.Email,
        Name = u.Name,
        FirstName = u.FirstName,
        LastName = u.LastName,
        Phone = u.Phone,
        Gender = u.Gender,
        Address = u.Address,
        ProfilePhoto = u.ProfilePhoto,
        Role = u.Role,
        IsActive = u.IsActive,
        CreatedAt = u.CreatedAt.ToString("o")
    };
}
