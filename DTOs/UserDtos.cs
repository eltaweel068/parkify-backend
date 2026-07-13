namespace Parkify.API.DTOs;

public class UserProfileResponse
{
    public Guid Id { get; init; }
    public string Email { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public string? FirstName { get; init; }
    public string? LastName { get; init; }
    public string? Phone { get; init; }
    public string? Gender { get; init; }
    public string? Address { get; init; }
    public string? ProfilePhoto { get; init; }
    public string Role { get; init; } = "user";
    public bool IsActive { get; init; } = true;
    public string? CreatedAt { get; init; }
}

public record CompleteProfileRequest(
    string FirstName,
    string LastName,
    string? Gender,
    string? Phone,
    string? Address,
    string? CarPlate,
    string? CarModel
);

public record UpdateProfileRequest(
    string? FirstName,
    string? LastName,
    string? Phone,
    string? Address,
    string? Email,
    string? Gender
);

public class CarResponse
{
    public Guid Id { get; init; }
    public string Plate { get; init; } = string.Empty;
    public string? Make { get; init; }
    public string? Model { get; init; }
    public int? Year { get; init; }
    public string? Color { get; init; }
    public bool IsDefault { get; init; }
}

public record CarCreateRequest(
    string Plate,
    string? Make,
    string? Model,
    int? Year,
    string? Color,
    bool IsDefault = false
);

public record CarUpdateRequest(
    string? Plate,
    string? Make,
    string? Model,
    int? Year,
    string? Color
);

public class PaymentMethodResponse
{
    public Guid Id { get; init; }
    public string CardType { get; init; } = string.Empty;
    public string? LastFour { get; init; }
    public string? CardHolderName { get; init; }
    public string? Expiry { get; init; }
    public bool IsDefault { get; init; }
}

public record PaymentMethodCreateRequest(
    string CardType,
    string? CardNumber,
    string? CardHolderName,
    int? ExpiryMonth,
    int? ExpiryYear,
    bool IsDefault = false
);
