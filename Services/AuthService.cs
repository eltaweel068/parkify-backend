using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Parkify.API.Data;
using Parkify.API.DTOs;
using Parkify.API.Models;
using BC = BCrypt.Net.BCrypt;

namespace Parkify.API.Services;

public class AuthService(AppDbContext db, IConfiguration config)
{
    private string SecretKey => config["Jwt:SecretKey"] ?? "local-dev-secret-key-12345";
    private string Issuer => config["Jwt:Issuer"] ?? "parkify-api";
    private string Audience => config["Jwt:Audience"] ?? "parkify-app";
    private int AccessExpiry => int.TryParse(config["Jwt:AccessTokenExpiryMinutes"], out var v) ? v : 60;
    private int RefreshExpiry => int.TryParse(config["Jwt:RefreshTokenExpiryDays"], out var v) ? v : 7;

    public async Task<User?> GetByIdAsync(Guid id) =>
        await db.Users.FindAsync(id);

    public async Task<User?> GetByEmailAsync(string email) =>
        await db.Users.FirstOrDefaultAsync(u => u.Email == email.ToLower());

    public async Task<TokenResponse> RegisterAsync(RegisterRequest req)
    {
        var existing = await GetByEmailAsync(req.Email);
        if (existing != null)
            throw new InvalidOperationException("Email already registered");

        var user = new User
        {
            Email = req.Email.ToLower(),
            Name = req.Name,
            Phone = req.Phone,
            PasswordHash = BC.HashPassword(req.Password),
            Role = "user"
        };
        db.Users.Add(user);
        await db.SaveChangesAsync();
        return BuildTokenResponse(user);
    }

    public async Task<TokenResponse> LoginAsync(LoginRequest req)
    {
        var user = await GetByEmailAsync(req.Email)
            ?? throw new UnauthorizedAccessException("Invalid credentials");

        if (!user.IsActive)
            throw new UnauthorizedAccessException("Account is suspended");

        if (user.PasswordHash == null || !BC.Verify(req.Password, user.PasswordHash))
            throw new UnauthorizedAccessException("Invalid credentials");

        return BuildTokenResponse(user);
    }

    public async Task<TokenResponse> RefreshAsync(string refreshToken)
    {
        var principal = ValidateToken(refreshToken, "refresh")
            ?? throw new UnauthorizedAccessException("Invalid refresh token");

        var userId = Guid.Parse(principal.FindFirst(ClaimTypes.NameIdentifier)!.Value);
        var user = await db.Users.FindAsync(userId)
            ?? throw new UnauthorizedAccessException("User not found");

        return BuildTokenResponse(user);
    }

    public async Task<TokenResponse> SocialLoginAsync(SocialLoginRequest req)
    {
        if (string.IsNullOrEmpty(req.Email))
            throw new InvalidOperationException("Email required for social login");

        var user = await GetByEmailAsync(req.Email);
        if (user == null)
        {
            user = new User
            {
                Email = req.Email.ToLower(),
                Name = req.Name ?? req.Email.Split('@')[0],
                Role = "user"
            };
            db.Users.Add(user);
            await db.SaveChangesAsync();
        }

        return BuildTokenResponse(user);
    }

    public async Task<string> SendResetCodeAsync(string? email, string? phone)
    {
        var code = Random.Shared.Next(100000, 999999).ToString();
        var reset = new ResetCode
        {
            Email = email?.ToLower(),
            Phone = phone,
            Code = code,
            ExpiresAt = DateTime.UtcNow.AddMinutes(15)
        };
        db.ResetCodes.Add(reset);
        await db.SaveChangesAsync();
        return code;
    }

    public async Task<bool> VerifyCodeAsync(string? email, string? phone, string code)
    {
        var reset = await db.ResetCodes.FirstOrDefaultAsync(r =>
            r.Code == code &&
            !r.IsUsed &&
            r.ExpiresAt > DateTime.UtcNow &&
            (email != null ? r.Email == email.ToLower() : r.Phone == phone));
        return reset != null;
    }

    public async Task ResetPasswordAsync(string? email, string? phone, string code, string newPassword)
    {
        var reset = await db.ResetCodes.FirstOrDefaultAsync(r =>
            r.Code == code &&
            !r.IsUsed &&
            r.ExpiresAt > DateTime.UtcNow &&
            (email != null ? r.Email == email.ToLower() : r.Phone == phone))
            ?? throw new InvalidOperationException("Invalid or expired code");

        reset.IsUsed = true;

        User? user = email != null
            ? await GetByEmailAsync(email)
            : await db.Users.FirstOrDefaultAsync(u => u.Phone == phone);

        if (user != null)
            user.PasswordHash = BC.HashPassword(newPassword);

        await db.SaveChangesAsync();
    }

    public async Task<User?> UpdateProfileAsync(Guid userId, UpdateProfileRequest req)
    {
        var user = await db.Users.FindAsync(userId);
        if (user == null) return null;

        if (req.FirstName != null) user.FirstName = req.FirstName;
        if (req.LastName != null) user.LastName = req.LastName;
        if (req.Phone != null) user.Phone = req.Phone;
        if (req.Address != null) user.Address = req.Address;
        if (req.Gender != null) user.Gender = req.Gender;
        if (req.Email != null) user.Email = req.Email.ToLower();
        if (req.FirstName != null || req.LastName != null)
            user.Name = $"{user.FirstName ?? ""} {user.LastName ?? ""}".Trim();

        await db.SaveChangesAsync();
        return user;
    }

    public async Task<User?> CompleteProfileAsync(Guid userId, CompleteProfileRequest req)
    {
        var user = await db.Users.FindAsync(userId);
        if (user == null) return null;

        user.FirstName = req.FirstName;
        user.LastName = req.LastName;
        user.Name = $"{req.FirstName} {req.LastName}".Trim();
        if (req.Gender != null) user.Gender = req.Gender;
        if (req.Phone != null) user.Phone = req.Phone;
        if (req.Address != null) user.Address = req.Address;

        if (!string.IsNullOrEmpty(req.CarPlate))
        {
            var existingCar = await db.Cars.FirstOrDefaultAsync(c => c.UserId == userId);
            if (existingCar == null)
            {
                db.Cars.Add(new Car
                {
                    UserId = userId,
                    LicensePlate = req.CarPlate,
                    Model = req.CarModel,
                    IsDefault = true
                });
            }
        }

        await db.SaveChangesAsync();
        return user;
    }

    public async Task ChangePasswordAsync(Guid userId, string currentPassword, string newPassword)
    {
        var user = await db.Users.FindAsync(userId)
            ?? throw new InvalidOperationException("User not found");

        if (user.PasswordHash == null || !BC.Verify(currentPassword, user.PasswordHash))
            throw new InvalidOperationException("Current password is incorrect");

        user.PasswordHash = BC.HashPassword(newPassword);
        await db.SaveChangesAsync();
    }

    public TokenResponse BuildTokenResponse(User user)
    {
        return new TokenResponse
        {
            AccessToken = CreateToken(user, "access", TimeSpan.FromMinutes(AccessExpiry)),
            RefreshToken = CreateToken(user, "refresh", TimeSpan.FromDays(RefreshExpiry)),
            TokenType = "bearer",
            ExpiresIn = AccessExpiry * 60,
            User = new { id = user.Id, email = user.Email, name = user.Name, role = user.Role }
        };
    }

    private string CreateToken(User user, string type, TimeSpan expiry)
    {
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(SecretKey));
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
            new Claim(ClaimTypes.Email, user.Email),
            new Claim(ClaimTypes.Role, user.Role),
            new Claim("type", type)
        };
        var token = new JwtSecurityToken(
            issuer: Issuer,
            audience: Audience,
            claims: claims,
            expires: DateTime.UtcNow.Add(expiry),
            signingCredentials: new SigningCredentials(key, SecurityAlgorithms.HmacSha256));
        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    private ClaimsPrincipal? ValidateToken(string token, string expectedType)
    {
        try
        {
            var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(SecretKey));
            var handler = new JwtSecurityTokenHandler();
            var principal = handler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = key,
                ValidateIssuer = true,
                ValidIssuer = Issuer,
                ValidateAudience = true,
                ValidAudience = Audience,
                ValidateLifetime = true
            }, out _);

            if (principal.FindFirst("type")?.Value != expectedType)
                return null;

            return principal;
        }
        catch
        {
            return null;
        }
    }
}
