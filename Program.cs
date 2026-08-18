using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using Parkify.API.Data;
using Parkify.API.Services;
using Parkify.API.WebSockets;

var builder = WebApplication.CreateBuilder(args);

// ─── Database ─────────────────────────────────────────────────────────────────
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// ─── JWT Authentication ───────────────────────────────────────────────────────
var jwtKey = builder.Configuration["Jwt:SecretKey"] ?? "local-dev-secret-key-12345";
var jwtIssuer = builder.Configuration["Jwt:Issuer"] ?? "parkify-api";
var jwtAudience = builder.Configuration["Jwt:Audience"] ?? "parkify-app";

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ValidateIssuer = true,
            ValidIssuer = jwtIssuer,
            ValidateAudience = true,
            ValidAudience = jwtAudience,
            ValidateLifetime = true,
            ClockSkew = TimeSpan.Zero
        };
    });

builder.Services.AddAuthorization();

// ─── CORS ─────────────────────────────────────────────────────────────────────
builder.Services.AddCors(o => o.AddDefaultPolicy(p =>
    p.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));

// ─── Services (Scoped per request) ────────────────────────────────────────────
builder.Services.AddScoped<AuthService>();
builder.Services.AddScoped<ParkingService>();
builder.Services.AddScoped<BookingService>();
builder.Services.AddScoped<NotificationService>();
builder.Services.AddScoped<AlertService>();
builder.Services.AddScoped<VehicleLogService>();
builder.Services.AddScoped<SupportService>();
builder.Services.AddScoped<FavoriteService>();
builder.Services.AddScoped<UserService>();

// ─── Singleton WebSocket Manager ──────────────────────────────────────────────
builder.Services.AddSingleton<ConnectionManager>();

// ─── Controllers + Swagger ────────────────────────────────────────────────────
builder.Services.AddControllers()
    .AddJsonOptions(o =>
    {
        o.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
        o.JsonSerializerOptions.DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull;
    });

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "Parkify API", Version = "v1", Description = "Smart Parking Management System" });
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        Description = "Enter your JWT access token"
    });
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme { Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" } },
            Array.Empty<string>()
        }
    });
});

var app = builder.Build();

// ─── Middleware Pipeline ──────────────────────────────────────────────────────
//if (app.Environment.IsDevelopment())
//{
    app.UseSwagger();
    app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "Parkify API v1"));
//}

app.UseCors();

app.UseWebSockets(new WebSocketOptions { KeepAliveInterval = TimeSpan.FromSeconds(30) });
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

// ─── Root & Health ────────────────────────────────────────────────────────────
app.MapGet("/", () => Results.Json(new
{
    message = "Welcome to Parkify API",
    version = "1.0.0",
    docs = "/swagger"
}));

app.MapGet("/health", () => Results.Json(new { status = "healthy", service = "parkify-api", version = "1.0.0" }));




// ─── WebSocket: Parking Updates ───────────────────────────────────────────────
app.Map("/ws/parking/{parkingId}", async (HttpContext context, string parkingId) =>
{
    if (!context.WebSockets.IsWebSocketRequest) { context.Response.StatusCode = 400; return; }
    var ws = await context.WebSockets.AcceptWebSocketAsync();
    var mgr = context.RequestServices.GetRequiredService<ConnectionManager>();
    var channel = $"parking:{parkingId}";
    mgr.Connect(ws, channel);
    try
    {
        await mgr.SendAsync(ws, new { type = "connected", parking_id = parkingId });
        await ReceiveLoopAsync(ws, async msg =>
        {
            if (msg.TryGetProperty("type", out var t) && t.GetString() == "ping")
                await mgr.SendAsync(ws, new { type = "pong" });
        });
    }
    finally { mgr.Disconnect(ws, channel); }
});

// ─── WebSocket: Admin ─────────────────────────────────────────────────────────
app.Map("/ws/admin", async (HttpContext context) =>
{
    if (!context.WebSockets.IsWebSocketRequest) { context.Response.StatusCode = 400; return; }
    var ws = await context.WebSockets.AcceptWebSocketAsync();
    var mgr = context.RequestServices.GetRequiredService<ConnectionManager>();
    mgr.Connect(ws, "admin");
    try
    {
        await mgr.SendAsync(ws, new { type = "connected", channel = "admin" });
        await ReceiveLoopAsync(ws, async msg =>
        {
            if (msg.TryGetProperty("type", out var t) && t.GetString() == "ping")
                await mgr.SendAsync(ws, new { type = "pong" });
        });
    }
    finally { mgr.Disconnect(ws, "admin"); }
});

// ─── WebSocket: Gate (ESP32) ──────────────────────────────────────────────────
app.Map("/ws/gate/{parkingId}", async (HttpContext context, string parkingId) =>
{
    if (!context.WebSockets.IsWebSocketRequest) { context.Response.StatusCode = 400; return; }

    var deviceKey = context.Request.Query["device_key"].ToString();
    var db = context.RequestServices.GetRequiredService<AppDbContext>();

    if (!Guid.TryParse(parkingId, out var parkingGuid))
    {
        await context.WebSockets.AcceptWebSocketAsync().ContinueWith(t => t.Result.CloseAsync(
            WebSocketCloseStatus.PolicyViolation, "Invalid parking id", CancellationToken.None));
        return;
    }

    var parking = await db.Parkings.FindAsync(parkingGuid);
    if (parking == null || parking.DeviceKey != deviceKey)
    {
        context.Response.StatusCode = 403;
        return;
    }

    var ws = await context.WebSockets.AcceptWebSocketAsync();
    var mgr = context.RequestServices.GetRequiredService<ConnectionManager>();
    var bookingService = context.RequestServices.GetRequiredService<BookingService>();
    var alertService = context.RequestServices.GetRequiredService<AlertService>();
    var notifService = context.RequestServices.GetRequiredService<NotificationService>();
    var vehicleLogService = context.RequestServices.GetRequiredService<VehicleLogService>();
    var parkingService = context.RequestServices.GetRequiredService<ParkingService>();

    var channel = $"gate:{parkingGuid}";
    mgr.Connect(ws, channel);

    try
    {
        await mgr.SendAsync(ws, new { type = "connected", parking_id = parkingGuid });

        await ReceiveLoopAsync(ws, async msg =>
        {
            if (!msg.TryGetProperty("type", out var typeEl)) return;
            var msgType = typeEl.GetString();

            switch (msgType)
            {
                case "ping":
                    await mgr.SendAsync(ws, new { type = "pong" });
                    break;

                case "gate_status":
                    await mgr.SendToChannelAsync("admin", new { type = "gate_update", parking_id = parkingGuid, data = msg });
                    break;

                case "slot_update":
                    await mgr.SendToChannelAsync($"parking:{parkingGuid}", new { type = "slot_update", parking_id = parkingGuid, data = msg });
                    await mgr.SendToChannelAsync("admin", new { type = "slot_update", parking_id = parkingGuid, data = msg });
                    break;

                case "plate_detected":
                    var plate = msg.TryGetProperty("plate", out var p) ? p.GetString() ?? "" : "";
                    var actionType = msg.TryGetProperty("action", out var a) ? a.GetString() ?? "entry" : "entry";
                    var gate = msg.TryGetProperty("gate", out var g) ? g.GetString() ?? "Gate A" : "Gate A";
                    double conf = msg.TryGetProperty("confidence", out var c) ? c.GetDouble() : 0.95;

                    await vehicleLogService.AddLogAsync(parkingGuid, plate, actionType, gate, conf);

                    bool verified = false;
                    Guid? bookingId = null;

                    if (actionType == "entry")
                    {
                        var booking = await bookingService.FindByPlateAsync(parkingGuid, plate, new[] { "confirmed" });
                        if (booking != null)
                        {
                            verified = true;
                            bookingId = booking.Id;
                            await bookingService.CheckInAsync(booking.Id);
                            await mgr.SendAsync(ws, new { type = "gate_command", gate_type = "entry", action = "open" });
                        }
                        else
                        {
                            await alertService.CreateAsync(parkingGuid, "security", "medium", $"Unregistered vehicle: {plate} at {gate}");
                        }
                    }
                    else if (actionType == "exit")
                    {
                        var booking = await bookingService.FindByPlateAsync(parkingGuid, plate, new[] { "active" });
                        if (booking != null)
                        {
                            verified = true;
                            bookingId = booking.Id;
                            await bookingService.CheckOutAsync(booking.Id);
                            await NotifyWatchersFromWs(db, parkingGuid, notifService, parking.Name);
                        }
                        await mgr.SendAsync(ws, new { type = "gate_command", gate_type = "exit", action = "open" });
                    }

                    await mgr.SendToChannelAsync("admin", new
                    {
                        type = "plate_detected",
                        parking_id = parkingGuid,
                        data = new { plate, action = actionType, gate, confidence = conf, verified, booking_id = bookingId }
                    });
                    break;

                case "fire_alert":
                    var fireMsg = msg.TryGetProperty("message", out var fm) ? fm.GetString() ?? "Fire detected" : "Fire detected";
                    await alertService.CreateAsync(parkingGuid, "fire", "critical", fireMsg);
                    await mgr.SendToChannelAsync("admin", new { type = "fire_alert", parking_id = parkingGuid, data = msg });
                    break;

                case "theft_alert":
                    var theftMsg = msg.TryGetProperty("message", out var tm) ? tm.GetString() ?? "Suspicious activity detected" : "Suspicious activity detected";
                    await alertService.CreateAsync(parkingGuid, "theft", "high", theftMsg);
                    await mgr.SendToChannelAsync("admin", new { type = "theft_alert", parking_id = parkingGuid, data = msg });
                    break;
            }
        });
    }
    finally
    {
        mgr.Disconnect(ws, channel);
    }
});

app.Run();

// ─── Helper: receive loop ─────────────────────────────────────────────────────
static async Task ReceiveLoopAsync(WebSocket ws, Func<JsonElement, Task> handler)
{
    var buffer = new byte[4096];
    while (ws.State == WebSocketState.Open)
    {
        try
        {
            var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
            if (result.MessageType == WebSocketMessageType.Close) break;
            if (result.MessageType != WebSocketMessageType.Text) continue;

            var json = Encoding.UTF8.GetString(buffer, 0, result.Count);
            if (string.IsNullOrWhiteSpace(json)) continue;

            var doc = JsonDocument.Parse(json);
            await handler(doc.RootElement);
        }
        catch (WebSocketException) { break; }
        catch (Exception) { /* ignore parse errors */ }
    }
}

static async Task NotifyWatchersFromWs(AppDbContext db, Guid parkingId, NotificationService notifService, string parkingName)
{
    var watchers = db.SpotWatchers.Where(w => w.ParkingId == parkingId).ToList();
    if (!watchers.Any()) return;
    var dataJson = JsonSerializer.Serialize(new { parking_id = parkingId });
    foreach (var w in watchers)
        await notifService.CreateAsync(w.UserId, "Spot Available!", $"A parking spot just opened at {parkingName}. Book now!", "booking", dataJson);
    db.SpotWatchers.RemoveRange(watchers);
    await db.SaveChangesAsync();
}
