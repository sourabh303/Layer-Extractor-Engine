using System;
using System.Text;
using Xunit;
using src_core.Services;

namespace src_core.Tests
{
    public class LicenseServiceTests
    {
        private readonly LicenseService _licenseService;

        public LicenseServiceTests()
        {
            _licenseService = new LicenseService();
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
