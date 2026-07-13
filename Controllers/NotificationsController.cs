using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Parkify.API.Services;

namespace Parkify.API.Controllers;

[ApiController]
[Route("api/v1/notifications")]
[Authorize]
public class NotificationsController(NotificationService notificationService) : ControllerBase
{
    private Guid UserId => Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    [HttpGet]
    public async Task<IActionResult> GetAll() => Ok(await notificationService.GetUserNotificationsAsync(UserId));

    [HttpGet("unread-count")]
    public async Task<IActionResult> UnreadCount()
    {
        var count = await notificationService.GetUnreadCountAsync(UserId);
        return Ok(new { count });
    }

    [HttpPut("{notificationId}/read")]
    public async Task<IActionResult> MarkRead(Guid notificationId)
    {
        var n = await notificationService.MarkReadAsync(notificationId, UserId);
        if (n == null) return NotFound(new { detail = "Notification not found" });
        return Ok(n);
    }

    [HttpPut("read-all")]
    public async Task<IActionResult> MarkAllRead()
    {
        var count = await notificationService.MarkAllReadAsync(UserId);
        return Ok(new { success = true, message = $"{count} notifications marked as read" });
    }

    [HttpDelete("{notificationId}")]
    public async Task<IActionResult> Delete(Guid notificationId)
    {
        if (!await notificationService.DeleteAsync(notificationId, UserId))
            return NotFound(new { detail = "Notification not found" });
        return Ok(new { success = true, message = "Notification deleted" });
    }
}
