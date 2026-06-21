using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using src_core.Services;

namespace src_core.Tests
{
    public class MockHttpMessageHandler : HttpMessageHandler
    {
        public Func<HttpRequestMessage, HttpResponseMessage>? SendAsyncFunc { get; set; }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            if (SendAsyncFunc != null)
            {
                return Task.FromResult(SendAsyncFunc(request));
            }
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound));
        }
    }

    public class LicenseServiceTests : IDisposable
    {
        private readonly LicenseService _licenseService;
        private readonly string _tempCacheDir;

        public LicenseServiceTests()
        {
            _tempCacheDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
            _licenseService = new LicenseService(new HttpClient(), _tempCacheDir, "https://test.supabase.co", "test-anon-key");
        }

        public void Dispose()
        {
            if (Directory.Exists(_tempCacheDir))
            {
                Directory.Delete(_tempCacheDir, true);
            }
        }

        [Fact]
        public async Task VerifyAndActivateAsync_ValidLicense_ReturnsTrueAndCaches()
        {
            // Arrange
            var mockHandler = new MockHttpMessageHandler();
            var httpClient = new HttpClient(mockHandler);
            var licenseService = new LicenseService(httpClient, _tempCacheDir, "https://test.supabase.co", "test-anon-key");

            var userId = "user-123";
            var machineId = "machine-456";
            var payloadJson = $"{{\"sub\":\"{userId}\"}}";
            var payloadBase64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(payloadJson));
            var jwt = $"header.{payloadBase64}.signature";

            mockHandler.SendAsyncFunc = req =>
            {
                if (req.RequestUri != null && req.RequestUri.PathAndQuery.Contains("/auth/v1/user"))
                {
                    return new HttpResponseMessage(HttpStatusCode.OK);
                }
                if (req.RequestUri != null && req.RequestUri.PathAndQuery.Contains("/rest/v1/licenses"))
                {
                    return new HttpResponseMessage(HttpStatusCode.OK)
                    {
                        Content = new StringContent($"[{{\"machine_id\":\"{machineId}\",\"trial_started_at\":\"{DateTimeOffset.UtcNow:O}\"}}]")
                    };
                }
                return new HttpResponseMessage(HttpStatusCode.NotFound);
            };

            // Act
            var result = await licenseService.VerifyAndActivateAsync(jwt, machineId);

            // Assert
            Assert.True(result);
            Assert.True(File.Exists(Path.Combine(_tempCacheDir, "license_cache.dat")));
        }

        [Fact]
        public async Task VerifyAndActivateAsync_InvalidJwt_ReturnsFalse()
        {
            // Arrange
            var mockHandler = new MockHttpMessageHandler();
            var httpClient = new HttpClient(mockHandler);
            var licenseService = new LicenseService(httpClient, _tempCacheDir, "https://test.supabase.co", "test-anon-key");

            var jwt = "invalid.jwt.token";
            var machineId = "machine-456";

            mockHandler.SendAsyncFunc = req => new HttpResponseMessage(HttpStatusCode.Unauthorized);

            // Act
            var result = await licenseService.VerifyAndActivateAsync(jwt, machineId);

            // Assert
            Assert.False(result);
            Assert.False(File.Exists(Path.Combine(_tempCacheDir, "license_cache.dat")));
        }

        [Fact]
        public async Task BootFromCacheAsync_ValidCache_ReturnsTrue()
        {
            // Arrange
            var mockHandler = new MockHttpMessageHandler();
            var httpClient = new HttpClient(mockHandler);
            var licenseService = new LicenseService(httpClient, _tempCacheDir, "https://test.supabase.co", "test-anon-key");

            var userId = "user-123";
            var machineId = "machine-456";
            var payloadJson = $"{{\"sub\":\"{userId}\"}}";
            var payloadBase64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(payloadJson));
            var jwt = $"header.{payloadBase64}.signature";

            mockHandler.SendAsyncFunc = req =>
            {
                if (req.RequestUri != null && req.RequestUri.PathAndQuery.Contains("/auth/v1/user")) return new HttpResponseMessage(HttpStatusCode.OK);
                if (req.RequestUri != null && req.RequestUri.PathAndQuery.Contains("/rest/v1/licenses"))
                    return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent($"[{{\"machine_id\":\"{machineId}\",\"trial_started_at\":\"{DateTimeOffset.UtcNow:O}\"}}]") };
                return new HttpResponseMessage(HttpStatusCode.NotFound);
            };

            // Act
            await licenseService.VerifyAndActivateAsync(jwt, machineId); // Cache it first
            var result = await licenseService.BootFromCacheAsync(machineId);

            // Assert
            Assert.True(result);
        }

        [Fact]
        public async Task BootFromCacheAsync_NoCache_ReturnsFalse()
        {
            // Arrange
            var licenseService = new LicenseService(new HttpClient(), _tempCacheDir, "https://test.supabase.co", "test-anon-key");

            // Act
            var result = await licenseService.BootFromCacheAsync("machine-456");

            // Assert
            Assert.False(result);
        }

        [Fact]
        public async Task GetCachedJwtAsync_ReturnsJwt()
        {
            // Arrange
            var mockHandler = new MockHttpMessageHandler();
            var httpClient = new HttpClient(mockHandler);
            var licenseService = new LicenseService(httpClient, _tempCacheDir, "https://test.supabase.co", "test-anon-key");

            var userId = "user-123";
            var machineId = "machine-456";
            var payloadJson = $"{{\"sub\":\"{userId}\"}}";
            var payloadBase64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(payloadJson));
            var jwt = $"header.{payloadBase64}.signature";

            mockHandler.SendAsyncFunc = req =>
            {
                if (req.RequestUri != null && req.RequestUri.PathAndQuery.Contains("/auth/v1/user")) return new HttpResponseMessage(HttpStatusCode.OK);
                if (req.RequestUri != null && req.RequestUri.PathAndQuery.Contains("/rest/v1/licenses"))
                    return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent($"[{{\"machine_id\":\"{machineId}\",\"trial_started_at\":\"{DateTimeOffset.UtcNow:O}\"}}]") };
                return new HttpResponseMessage(HttpStatusCode.NotFound);
            };

            // Act
            await licenseService.VerifyAndActivateAsync(jwt, machineId); // Cache it first
            var result = await licenseService.GetCachedJwtAsync(machineId);

            // Assert
            Assert.Equal(jwt, result);
        }

        [Theory]
        [InlineData("")]
        [InlineData("invalid_jwt_no_dots")]
        public void ExtractUserIdFromJwt_InvalidFormat_ReturnsEmptyString(string jwt)
        {
            // Act
            var result = _licenseService.ExtractUserIdFromJwt(jwt);

            // Assert
            Assert.Equal(string.Empty, result);
        }

        [Fact]
        public void ExtractUserIdFromJwt_ValidBase64MissingSub_ReturnsEmptyString()
        {
            // Arrange
            var payloadJson = "{\"name\":\"John Doe\"}";
            var payloadBase64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(payloadJson));
            var jwt = $"header.{payloadBase64}.signature";

            // Act
            var result = _licenseService.ExtractUserIdFromJwt(jwt);

            // Assert
            Assert.Equal(string.Empty, result);
        }

        [Fact]
        public void ExtractUserIdFromJwt_ValidPayloadWithSub_ReturnsUserId()
        {
            // Arrange
            var expectedUserId = "user-12345";
            var payloadJson = $"{{\"sub\":\"{expectedUserId}\",\"name\":\"John Doe\"}}";
            var payloadBase64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(payloadJson));
            var jwt = $"header.{payloadBase64}.signature";

            // Act
            var result = _licenseService.ExtractUserIdFromJwt(jwt);

            // Assert
            Assert.Equal(expectedUserId, result);
        }

        [Fact]
        public void ExtractUserIdFromJwt_InvalidBase64Payload_ReturnsEmptyString()
        {
            // Arrange
            var jwt = "header.invalid_base64!@#.signature";

            // Act
            var result = _licenseService.ExtractUserIdFromJwt(jwt);

            // Assert
            Assert.Equal(string.Empty, result);
        }

        [Fact]
        public void ExtractUserIdFromJwt_MalformedJsonPayload_ReturnsEmptyString()
        {
            // Arrange
            var payloadJson = "{\"sub\":\"user-12345\", invalid json}";
            var payloadBase64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(payloadJson));
            var jwt = $"header.{payloadBase64}.signature";

            // Act
            var result = _licenseService.ExtractUserIdFromJwt(jwt);

            // Assert
            Assert.Equal(string.Empty, result);
        }

        [Fact]
        public void ExtractUserIdFromJwt_Base64PaddingRequired_ReturnsUserId()
        {
            // Arrange
            var expectedUserId = "user-123";
            var payloadJson = $"{{\"sub\":\"{expectedUserId}\"}}";
            // Normal base64 might have padding '='. The Extract method logic handles replacing and adding padding.
            var payloadBase64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(payloadJson));

            // To test the padding logic:
            // payloadBase64 with length % 4 == 2 or 3
            // "eyJzdWIiOiJ1c2VyLTEyMyJ9" has length 24 (%4 == 0).
            // Let's create a payload that produces length % 4 == 2 or 3 when stripped of padding.

            var payloadNoPadding = payloadBase64.TrimEnd('='); // e.g. length could be 22 or 23

            // The jwt payload might have - and _ instead of + and / (Base64Url encoding)
            var base64UrlPayload = payloadNoPadding.Replace('+', '-').Replace('/', '_');

            var jwt = $"header.{base64UrlPayload}.signature";

            // Act
            var result = _licenseService.ExtractUserIdFromJwt(jwt);

            // Assert
            Assert.Equal(expectedUserId, result);
        }
    }
}
