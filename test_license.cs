using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

class Program
{
    static void Main()
    {
        var machineId = "test-machine-id";
        var plainText = "Hello World License";

        var salt = new byte[16];
        RandomNumberGenerator.Fill(salt);

        var key = DeriveKey(machineId, salt);
        using var aes = Aes.Create();
        aes.Key = key;
        aes.GenerateIV();

        using var encryptor = aes.CreateEncryptor(aes.Key, aes.IV);
        using var ms = new MemoryStream();
        ms.Write(salt, 0, salt.Length); // Prepend Salt
        ms.Write(aes.IV, 0, aes.IV.Length); // Prepend IV
        using (var cs = new CryptoStream(ms, encryptor, CryptoStreamMode.Write))
        using (var sw = new StreamWriter(cs))
        {
            sw.Write(plainText);
        }
        var cipherData = ms.ToArray();

        // Decrypt
        var decSalt = new byte[16];
        Array.Copy(cipherData, 0, decSalt, 0, decSalt.Length);

        var decKey = DeriveKey(machineId, decSalt);
        using var decAes = Aes.Create();
        decAes.Key = decKey;

        var decIv = new byte[decAes.BlockSize / 8];
        Array.Copy(cipherData, decSalt.Length, decIv, 0, decIv.Length);
        decAes.IV = decIv;

        using var decryptor = decAes.CreateDecryptor(decAes.Key, decAes.IV);
        var offset = decSalt.Length + decIv.Length;
        using var decMs = new MemoryStream(cipherData, offset, cipherData.Length - offset);
        using var decCs = new CryptoStream(decMs, decryptor, CryptoStreamMode.Read);
        using var sr = new StreamReader(decCs);
        var decrypted = sr.ReadToEnd();

        Console.WriteLine(decrypted == plainText ? "SUCCESS" : "FAILED");
    }

    static byte[] DeriveKey(string machineId, byte[] salt)
    {
        using var pbkdf2 = new Rfc2898DeriveBytes(machineId, salt, 100000, HashAlgorithmName.SHA256);
        return pbkdf2.GetBytes(32);
    }
}
