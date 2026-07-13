using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace Parkify.API.WebSockets;

public class ConnectionManager
{
    private readonly Dictionary<string, HashSet<WebSocket>> _connections = new();
    private readonly object _lock = new();

    public void Connect(WebSocket ws, string channel)
    {
        lock (_lock)
        {
            if (!_connections.TryGetValue(channel, out var set))
                _connections[channel] = set = new HashSet<WebSocket>();
            set.Add(ws);
        }
    }

    public void Disconnect(WebSocket ws, string channel)
    {
        lock (_lock)
        {
            if (_connections.TryGetValue(channel, out var set))
                set.Remove(ws);
        }
    }

    public async Task SendToChannelAsync(string channel, object message)
    {
        List<WebSocket> sockets;
        lock (_lock)
        {
            if (!_connections.TryGetValue(channel, out var set)) return;
            sockets = set.Where(ws => ws.State == WebSocketState.Open).ToList();
        }

        var json = JsonSerializer.Serialize(message, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower });
        var bytes = Encoding.UTF8.GetBytes(json);

        foreach (var ws in sockets)
        {
            try
            {
                await ws.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
            }
            catch
            {
                lock (_lock)
                {
                    if (_connections.TryGetValue(channel, out var set))
                        set.Remove(ws);
                }
            }
        }
    }

    public async Task SendAsync(WebSocket ws, object message)
    {
        var json = JsonSerializer.Serialize(message, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower });
        var bytes = Encoding.UTF8.GetBytes(json);
        await ws.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
    }
}
