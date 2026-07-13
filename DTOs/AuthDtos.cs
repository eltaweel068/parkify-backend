namespace Parkify.API.DTOs;

public record RegisterRequest(string Email, string Name, string Password, string? Phone);

public record LoginRequest(string Email, string Password);

public record RefreshTokenRequest(string RefreshToken);

public record SocialLoginRequest(string Provider, string Token, string? Name, string? Email);

public record ForgotPasswordEmailRequest(string Email);

public record ForgotPasswordPhoneRequest(string Phone);

public record VerifyCodeRequest(string? Email, string? Phone, string Code);

public record ResendCodeRequest(string? Email, string? Phone);

public record ResetPasswordRequest(string? Email, string? Phone, string Code, string NewPassword);

public record ChangePasswordRequest(string CurrentPassword, string NewPassword);

public class TokenResponse
{
    public string AccessToken { get; init; } = string.Empty;
    public string RefreshToken { get; init; } = string.Empty;
    public string TokenType { get; init; } = "bearer";
    public int ExpiresIn { get; init; }
    public object User { get; init; } = new();
}
