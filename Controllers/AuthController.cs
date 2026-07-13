using Microsoft.AspNetCore.Mvc;
using Parkify.API.DTOs;
using Parkify.API.Services;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/auth")]
public class AuthController(AuthService authService) : ControllerBase
{
    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] RegisterRequest req)
    {
        try
        {
            return Ok(await authService.RegisterAsync(req));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { detail = ex.Message });
        }
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginRequest req)
    {
        try
        {
            return Ok(await authService.LoginAsync(req));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(new { detail = ex.Message });
        }
    }

    [HttpPost("refresh")]
    public async Task<IActionResult> Refresh([FromBody] RefreshTokenRequest req)
    {
        try
        {
            return Ok(await authService.RefreshAsync(req.RefreshToken));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(new { detail = ex.Message });
        }
    }

    [HttpPost("social")]
    public async Task<IActionResult> Social([FromBody] SocialLoginRequest req)
    {
        try
        {
            return Ok(await authService.SocialLoginAsync(req));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { detail = ex.Message });
        }
    }

    [HttpPost("forgot-password/email")]
    public async Task<IActionResult> ForgotEmail([FromBody] ForgotPasswordEmailRequest req)
    {
        var code = await authService.SendResetCodeAsync(req.Email, null);
        return Ok(new { success = true, message = $"Reset code sent to {req.Email}", code });
    }

    [HttpPost("forgot-password/phone")]
    public async Task<IActionResult> ForgotPhone([FromBody] ForgotPasswordPhoneRequest req)
    {
        var code = await authService.SendResetCodeAsync(null, req.Phone);
        return Ok(new { success = true, message = $"Reset code sent to {req.Phone}", code });
    }

    [HttpPost("verify-code")]
    public async Task<IActionResult> VerifyCode([FromBody] VerifyCodeRequest req)
    {
        var verified = await authService.VerifyCodeAsync(req.Email, req.Phone, req.Code);
        return Ok(new { success = true, verified, message = verified ? "Code verified" : "Invalid or expired code" });
    }

    [HttpPost("resend-code")]
    public async Task<IActionResult> ResendCode([FromBody] ResendCodeRequest req)
    {
        var code = await authService.SendResetCodeAsync(req.Email, req.Phone);
        return Ok(new { success = true, message = "Code resent", code });
    }

    [HttpPost("reset-password")]
    public async Task<IActionResult> ResetPassword([FromBody] ResetPasswordRequest req)
    {
        try
        {
            await authService.ResetPasswordAsync(req.Email, req.Phone, req.Code, req.NewPassword);
            return Ok(new { success = true, message = "Password reset successfully" });
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { detail = ex.Message });
        }
    }
}
