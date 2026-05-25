using System.Net;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;

var builder = WebApplication.CreateBuilder(args);

builder.WebHost.ConfigureKestrel(serverOptions =>
{
    serverOptions.Listen(IPAddress.Loopback, 0); // Bind to dynamic port on localhost ONLY
});

var app = builder.Build();

app.Lifetime.ApplicationStarted.Register(() =>
{
    var server = app.Services.GetRequiredService<IServer>();
    var addressFeature = server.Features.Get<IServerAddressesFeature>();
    var address = addressFeature?.Addresses.FirstOrDefault();
    if (address != null)
    {
        var uri = new Uri(address);
        Console.WriteLine($"SIDECAR_PORT={uri.Port}");
    }
});

app.Run();
