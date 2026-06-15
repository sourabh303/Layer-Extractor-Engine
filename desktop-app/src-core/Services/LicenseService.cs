using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

[assembly: System.Runtime.CompilerServices.InternalsVisibleTo("src-core.Tests")]

namespace src_core.Services
{
    public class LicenseService
    {
        private readonly HttpClient _httpClient;
        private readonly string _supabaseUrl;
        private readonly string _supabaseAnonKey;
        private readonly string _cacheDirectory;
        private readonly string _cacheFilePath;
        private const string ApplicationSalt = "jules_secret_salt_9x!L"; // Hardcoded salt for PBKDF2

        public LicenseService() : this(new HttpClient(), null)
        {
        }

        internal LicenseService(HttpClient httpClient, string? cacheDirectoryOverride, string? supabaseUrlOverride = null, string? supabaseAnonKeyOverride = null)
        {
            _httpClient = httpClient;

            _supabaseUrl = supabaseUrlOverride ?? Environment.GetEnvironmentVariable("VITE_SUPABASE_URL") ?? string.Empty;
            if (string.IsNullOrEmpty(_supabaseUrl))
            {
                throw new InvalidOperationException("CRITICAL: VITE_SUPABASE_URL environment variable is missing.");
            }

            _supabaseAnonKey = supabaseAnonKeyOverride ?? Environment.GetEnvironmentVariable("VITE_SUPABASE_ANON_KEY") ?? string.Empty;
            if (string.IsNullOrEmpty(_supabaseAnonKey))
            {
                throw new InvalidOperationException("CRITICAL: VITE_SUPABASE_ANON_KEY environment variable is missing.");
            }

            _cacheDirectory = cacheDirectoryOverride ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AITextileExtractor");
            _cacheFilePath = Path.Combine(_cacheDirectory, "license_cache.dat");

            if (!Directory.Exists(_cacheDirectory))
            {
                Directory.CreateDirectory(_cacheDirectory);
            }
        }

        public async Task<bool> VerifyAndActivateAsync(string jwt, string machineId)
        {
            // 1. Verify JWT via Supabase Auth API
            var isValidToken = await VerifyJwtWithSupabaseAsync(jwt);
            if (!isValidToken) return false;

            // 2. We extract the user_id from the valid JWT locally to query the licenses table
            var userId = ExtractUserIdFromJwt(jwt);
            if (string.IsNullOrEmpty(userId)) return false;

            // 3. Verify Trial / Hardware Binding via Supabase REST API
            var isLicenseValid = await VerifyLicenseWithSupabaseAsync(jwt, userId, machineId);
            if (!isLicenseValid) return false;

            // 4. Cache it locally
            await SaveCacheAsync(jwt, machineId);
            return true;
        }

        public async Task<bool> BootFromCacheAsync(string machineId)
        {
            try
            {
                if (!File.Exists(_cacheFilePath)) return false;

                var encryptedData = await File.ReadAllBytesAsync(_cacheFilePath);
                var decryptedJson = Decrypt(encryptedData, machineId);
                var cache = JsonSerializer.Deserialize<CachePayload>(decryptedJson);

                if (cache == null) return false;

                // Check 7-day grace period
                if ((DateTime.UtcNow - cache.ValidatedAt).TotalDays > 7)
                {
                    // Cache expired, needs network re-verification
                    return false;
                }

                // Cache valid
                return true;
            }
            catch
            {
                return false;
            }
        }

        public async Task<string?> GetCachedJwtAsync(string machineId)
        {
            try
            {
                if (!File.Exists(_cacheFilePath)) return null;

                var encryptedData = await File.ReadAllBytesAsync(_cacheFilePath);
                var decryptedJson = Decrypt(encryptedData, machineId);
                var cache = JsonSerializer.Deserialize<CachePayload>(decryptedJson);

                return cache?.Jwt;
            }
            catch
            {
                return null;
            }
        }

        private async Task<bool> VerifyJwtWithSupabaseAsync(string jwt)
        {
            try
            {
                using var request = new HttpRequestMessage(HttpMethod.Get, $"{_supabaseUrl}/auth/v1/user");
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", jwt);
                request.Headers.Add("apikey", _supabaseAnonKey);

                var response = await _httpClient.SendAsync(request);
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private async Task<bool> VerifyLicenseWithSupabaseAsync(string jwt, string userId, string machineId)
        {
            try
            {
                // Note: We use the REST API here via GET to check the license table
                using var request = new HttpRequestMessage(HttpMethod.Get, $"{_supabaseUrl}/rest/v1/licenses?user_id=eq.{userId}");
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", jwt);
                request.Headers.Add("apikey", _supabaseAnonKey);

                var response = await _httpClient.SendAsync(request);
                if (!response.IsSuccessStatusCode) return false;

                var jsonString = await response.Content.ReadAsStringAsync();
                var doc = JsonDocument.Parse(jsonString);
                var root = doc.RootElement;

                if (root.ValueKind == JsonValueKind.Array && root.GetArrayLength() > 0)
                {
                    var license = root[0];

                    // Hardware binding check
                    if (license.TryGetProperty("machine_id", out var dbMachineIdElement))
                    {
                        var dbMachineId = dbMachineIdElement.GetString();
                        if (!string.IsNullOrEmpty(dbMachineId) && dbMachineId != machineId)
                        {
                            return false; // Bound to another machine
                        }
                    }

                    // Trial window check
                    if (license.TryGetProperty("trial_started_at", out var trialStartedElement))
                    {
                        if (trialStartedElement.TryGetDateTimeOffset(out var trialStartedAt))
                        {
                            if ((DateTimeOffset.UtcNow - trialStartedAt).TotalDays > 30)
                            {
                                return false; // Trial expired
                            }
                        }
                    }

                    // If machine_id is null in DB, we should theoretically bind it here using a PATCH request.
                    // For the scope of this step, we will assume validity if the trial is active.
                    if (!license.TryGetProperty("machine_id", out _) || license.GetProperty("machine_id").ValueKind == JsonValueKind.Null)
                    {
                        await BindMachineIdAsync(jwt, userId, machineId);
                    }

                    return true;
                }

                return false;
            }
            catch
            {
                return false;
            }
        }

        private async Task BindMachineIdAsync(string jwt, string userId, string machineId)
        {
            try
            {
                using var request = new HttpRequestMessage(HttpMethod.Patch, $"{_supabaseUrl}/rest/v1/licenses?user_id=eq.{userId}");
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", jwt);
                request.Headers.Add("apikey", _supabaseAnonKey);
                request.Headers.Add("Prefer", "return=minimal");

                var payload = new { machine_id = machineId };
                request.Content = JsonContent.Create(payload);

                await _httpClient.SendAsync(request);
            }
            catch { }
        }

        internal string ExtractUserIdFromJwt(string jwt)
        {
            try
            {
                var parts = jwt.Split('.');
                if (parts.Length < 2) return string.Empty;

                var payloadStr = parts[1];
                payloadStr = payloadStr.Replace('-', '+').Replace('_', '/');
                switch (payloadStr.Length % 4)
                {
                    case 2: payloadStr += "=="; break;
                    case 3: payloadStr += "="; break;
                }

                var payloadBytes = Convert.FromBase64String(payloadStr);
                var payloadJson = Encoding.UTF8.GetString(payloadBytes);
                var doc = JsonDocument.Parse(payloadJson);

                if (doc.RootElement.TryGetProperty("sub", out var sub))
                {
                    return sub.GetString() ?? string.Empty;
                }

                return string.Empty;
            }
            catch
            {
                return string.Empty;
            }
        }

        private async Task SaveCacheAsync(string jwt, string machineId)
        {
            var cachePayload = new CachePayload
            {
                Jwt = jwt,
                ValidatedAt = DateTime.UtcNow
            };

            var json = JsonSerializer.Serialize(cachePayload);
            var encryptedBytes = Encrypt(json, machineId);
            await File.WriteAllBytesAsync(_cacheFilePath, encryptedBytes);
        }

        private byte[] Encrypt(string plainText, string machineId)
        {
            var key = DeriveKey(machineId);
            using var aes = Aes.Create();
            aes.Key = key;
            aes.GenerateIV();

            using var encryptor = aes.CreateEncryptor(aes.Key, aes.IV);
            using var ms = new MemoryStream();
            ms.Write(aes.IV, 0, aes.IV.Length); // Prepend IV
            using (var cs = new CryptoStream(ms, encryptor, CryptoStreamMode.Write))
            using (var sw = new StreamWriter(cs))
            {
                sw.Write(plainText);
            }
            return ms.ToArray();
        }

        private string Decrypt(byte[] cipherData, string machineId)
        {
            var key = DeriveKey(machineId);
            using var aes = Aes.Create();
            aes.Key = key;

            var iv = new byte[aes.BlockSize / 8];
            Array.Copy(cipherData, 0, iv, 0, iv.Length);
            aes.IV = iv;

            using var decryptor = aes.CreateDecryptor(aes.Key, aes.IV);
            using var ms = new MemoryStream(cipherData, iv.Length, cipherData.Length - iv.Length);
            using var cs = new CryptoStream(ms, decryptor, CryptoStreamMode.Read);
            using var sr = new StreamReader(cs);
            return sr.ReadToEnd();
        }

        private byte[] DeriveKey(string machineId)
        {
            // Cross-platform key derivation using PBKDF2 (Rfc2898DeriveBytes)
            var saltBytes = Encoding.UTF8.GetBytes(ApplicationSalt);
            using var pbkdf2 = new Rfc2898DeriveBytes(machineId, saltBytes, 100000, HashAlgorithmName.SHA256);
            return pbkdf2.GetBytes(32); // 256-bit key
        }

        private class CachePayload
        {
            public string Jwt { get; set; } = string.Empty;
            public DateTime ValidatedAt { get; set; }
        }
    }
}
