using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Models;
using Microsoft.AspNetCore.Mvc;
using src_core.Services;

var builder = WebApplication.CreateBuilder(args);

// Parse --ipc-secret from command line arguments
var ipcSecret = "";
for (int i = 0; i < args.Length; i++)
{
    if (args[i] == "--ipc-secret" && i + 1 < args.Length)
    {
        ipcSecret = args[i + 1];
        break;
    }
}

builder.Services.AddHttpClient();
builder.Services.AddSingleton<LicenseService>();
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        // SECURITY: Do not use AllowAnyOrigin(). Restrict origins to prevent Local API Hijacking
        // and cross-origin attacks from malicious websites making requests to the local sidecar.
        policy.WithOrigins("http://localhost:5173", "tauri://localhost", "https://tauri.localhost", "http://tauri.localhost")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

builder.WebHost.ConfigureKestrel(serverOptions =>
{
    serverOptions.Listen(IPAddress.Loopback, 0); // Bind to dynamic port on localhost ONLY
});

var app = builder.Build();

app.UseCors();

// Add IPC Secret Middleware
app.Use(async (context, next) =>
{
    // Skip OPTIONS requests as they are CORS preflight and don't carry custom headers
    if (context.Request.Method == "OPTIONS")
    {
        await next(context);
        return;
    }

    if (context.Request.Path.StartsWithSegments("/api"))
    {
        if (!context.Request.Headers.TryGetValue("X-IPC-Secret", out var providedSecret))
        {
            context.Response.StatusCode = 401;
            await context.Response.WriteAsync("Unauthorized: Invalid IPC Secret");
            return;
        }

        var providedBytes = Encoding.UTF8.GetBytes(providedSecret.ToString());
        var secretBytes = Encoding.UTF8.GetBytes(ipcSecret);

        if (providedBytes.Length != secretBytes.Length ||
            !CryptographicOperations.FixedTimeEquals(providedBytes, secretBytes))
        {
            context.Response.StatusCode = 401;
            await context.Response.WriteAsync("Unauthorized: Invalid IPC Secret");
            return;
        }
    }
    await next(context);
});

int pythonPort = src_core.NetworkUtilities.GetAvailablePort();
Process? pythonProcess = null;

app.Lifetime.ApplicationStarted.Register(() =>
{
    var server = app.Services.GetRequiredService<IServer>();
    var addressFeature = server.Features.Get<IServerAddressesFeature>();
    var address = addressFeature?.Addresses.FirstOrDefault();
    if (address != null)
    {
        var uri = new Uri(address);
        Console.WriteLine($"SIDECAR_PORT={uri.Port}");
        Console.Out.Flush();
    }
});

void StartPythonMLService()
{
    if (pythonProcess != null && !pythonProcess.HasExited) return;

    Console.WriteLine($"Starting Python ML Service on port {pythonPort}...");
    var mlServicePath = Path.GetFullPath(Path.Combine(app.Environment.ContentRootPath, "../../ml-service"));

    var startInfo = new ProcessStartInfo
    {
        FileName = "python3",
        Arguments = $"main.py --port {pythonPort}",
        WorkingDirectory = mlServicePath,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        UseShellExecute = false,
        CreateNoWindow = true
    };
    startInfo.Environment["IPC_SECRET"] = ipcSecret;

    pythonProcess = new Process { StartInfo = startInfo };
    pythonProcess.Start();
}

app.MapPost("/api/license/activate", async ([FromBody] ActivateRequest req, LicenseService licenseService) =>
{
    var isValid = await licenseService.VerifyAndActivateAsync(req.Jwt, req.MachineId);
    if (isValid)
    {
        StartPythonMLService();
        return Results.Ok(new { success = true });
    }
    return Results.Unauthorized();
});

app.MapPost("/api/boot", async ([FromBody] BootRequest req, LicenseService licenseService) =>
{
    var isValid = await licenseService.BootFromCacheAsync(req.MachineId);
    if (!isValid)
    {
        // Try network re-verification
        isValid = await licenseService.VerifyAndActivateAsync(req.Jwt, req.MachineId);
    }

    if (isValid)
    {
        StartPythonMLService();
        return Results.Ok(new { success = true });
    }
    return Results.Unauthorized();
});

app.MapGet("/api/status", async (IHttpClientFactory clientFactory) =>
{
    var client = clientFactory.CreateClient();
    client.DefaultRequestHeaders.Add("X-IPC-Secret", ipcSecret);
    var response = await client.GetAsync($"http://127.0.0.1:{pythonPort}/status");
    if (response.IsSuccessStatusCode)
    {
        var result = await response.Content.ReadAsStringAsync();
        return Results.Content(result, "application/json");
    }
    return Results.StatusCode((int)response.StatusCode);
});

app.Lifetime.ApplicationStopping.Register(() =>
{
    if (pythonProcess != null && !pythonProcess.HasExited)
    {
        pythonProcess.Kill();
    }
});

app.MapPost("/api/extract", async ([FromBody] ExtractionRequest request, IHttpClientFactory clientFactory) =>
{
    var client = clientFactory.CreateClient();
    client.DefaultRequestHeaders.Add("X-IPC-Secret", ipcSecret);
    var response = await client.PostAsJsonAsync($"http://127.0.0.1:{pythonPort}/extract", request);
    if (response.IsSuccessStatusCode)
    {
        var result = await response.Content.ReadAsStringAsync();
        return Results.Content(result, "application/json");
    }
    return Results.StatusCode((int)response.StatusCode);
});

app.Run();

public partial class Program { }
