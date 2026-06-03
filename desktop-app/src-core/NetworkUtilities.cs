using System.Net;
using System.Net.Sockets;

namespace src_core
{
    public static class NetworkUtilities
    {
        public static int GetAvailablePort()
        {
            var listener = new TcpListener(IPAddress.Loopback, 0);
            listener.Start();
            int port = ((IPEndPoint)listener.LocalEndpoint).Port;
            listener.Stop();
            return port;
        }
    }
}
