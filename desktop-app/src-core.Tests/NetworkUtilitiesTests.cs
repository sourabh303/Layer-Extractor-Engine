using System.Net;
using System.Net.Sockets;
using Xunit;
using src_core;

namespace src_core.Tests
{
    public class NetworkUtilitiesTests
    {
        [Fact]
        public void GetAvailablePort_ReturnsValidPortInRange()
        {
            // Act
            int port = NetworkUtilities.GetAvailablePort();

            // Assert
            Assert.True(port > 0 && port <= 65535, $"Expected port to be in range 1-65535, but got {port}");
        }

        [Fact]
        public void GetAvailablePort_WhenPortIsBound_ReturnsDifferentAvailablePort()
        {
            // Arrange
            // Get an available port first
            int firstPort = NetworkUtilities.GetAvailablePort();

            // Manually bind to it
            var listener = new TcpListener(IPAddress.Loopback, firstPort);
            listener.Start();

            try
            {
                // Act
                // Get another port while the first is occupied
                int secondPort = NetworkUtilities.GetAvailablePort();

                // Assert
                Assert.NotEqual(firstPort, secondPort);
                Assert.True(secondPort > 0 && secondPort <= 65535, $"Expected second port to be in range 1-65535, but got {secondPort}");
            }
            finally
            {
                // Clean up
                listener.Stop();
            }
        }
    }
}
