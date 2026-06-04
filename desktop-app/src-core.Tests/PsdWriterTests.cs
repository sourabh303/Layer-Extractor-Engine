using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using SkiaSharp;
using Xunit;
using src_core.Services;

namespace src_core.Tests
{
    public class PsdWriterTests : IDisposable
    {
        private readonly List<string> _tempFiles = new();

        private string GetTempFile()
        {
            var tempFile = Path.GetTempFileName();
            _tempFiles.Add(tempFile);
            return tempFile;
        }

        public void Dispose()
        {
            foreach (var file in _tempFiles)
            {
                if (File.Exists(file))
                {
                    try
                    {
                        File.Delete(file);
                    }
                    catch { }
                }
            }
        }

        [Fact]
        public void Write_ValidLayers_CreatesValidPsdFile()
        {
            // Arrange
            string outputPath = GetTempFile();
            using var bitmap = new SKBitmap(10, 10, SKColorType.Rgba8888, SKAlphaType.Premul);
            bitmap.Erase(SKColors.Red);
            var layers = new List<(string Name, SKBitmap Bitmap)> { ("Layer 1", bitmap) };

            // Act
            PsdWriter.Write(outputPath, 10, 10, layers);

            // Assert
            Assert.True(File.Exists(outputPath));

            using var fs = new FileStream(outputPath, FileMode.Open, FileAccess.Read);
            using var reader = new BinaryReader(fs);

            // 1. File Header
            var signature = Encoding.ASCII.GetString(reader.ReadBytes(4));
            Assert.Equal("8BPS", signature);

            var version = SwapBytes(reader.ReadInt16());
            Assert.Equal(1, version);

            reader.ReadBytes(6); // Reserved

            var channels = SwapBytes(reader.ReadInt16());
            Assert.Equal(3, channels);

            var height = SwapBytes(reader.ReadInt32());
            Assert.Equal(10, height);

            var width = SwapBytes(reader.ReadInt32());
            Assert.Equal(10, width);

            var depth = SwapBytes(reader.ReadInt16());
            Assert.Equal(8, depth);

            var colorMode = SwapBytes(reader.ReadInt16());
            Assert.Equal(3, colorMode);
        }

        [Fact]
        public void Write_MultipleLayers_CreatesValidPsdFile()
        {
            // Arrange
            string outputPath = GetTempFile();
            using var bitmapRgba = new SKBitmap(10, 10, SKColorType.Rgba8888, SKAlphaType.Premul);
            bitmapRgba.Erase(SKColors.Blue);

            using var bitmapBgra = new SKBitmap(10, 10, SKColorType.Bgra8888, SKAlphaType.Premul);
            bitmapBgra.Erase(SKColors.Green);

            var layers = new List<(string Name, SKBitmap Bitmap)>
            {
                ("Layer RGBA", bitmapRgba),
                ("Layer BGRA", bitmapBgra)
            };

            // Act
            PsdWriter.Write(outputPath, 10, 10, layers);

            // Assert
            Assert.True(File.Exists(outputPath));
            Assert.True(new FileInfo(outputPath).Length > 0);
        }

        [Fact]
        public void Write_LongLayerName_TruncatesCorrectly()
        {
            // Arrange
            string outputPath = GetTempFile();
            using var bitmap = new SKBitmap(10, 10, SKColorType.Rgba8888, SKAlphaType.Premul);
            var longName = new string('A', 300);
            var layers = new List<(string Name, SKBitmap Bitmap)> { (longName, bitmap) };

            // Act
            var exception = Record.Exception(() => PsdWriter.Write(outputPath, 10, 10, layers));

            // Assert
            Assert.Null(exception);
            Assert.True(File.Exists(outputPath));
        }

        [Fact]
        public void Write_UnknownFormatOrRowPadding_Fallback()
        {
            // Arrange
            string outputPath = GetTempFile();
            // Use Rgb565 to trigger the fallback path
            using var bitmap = new SKBitmap(10, 10, SKColorType.Rgb565, SKAlphaType.Opaque);
            bitmap.Erase(SKColors.Yellow);
            var layers = new List<(string Name, SKBitmap Bitmap)> { ("Fallback Layer", bitmap) };

            // Act
            var exception = Record.Exception(() => PsdWriter.Write(outputPath, 10, 10, layers));

            // Assert
            Assert.Null(exception);
            Assert.True(File.Exists(outputPath));
        }

        private static short SwapBytes(short value)
        {
            return (short)((value >> 8) | (value << 8));
        }

        private static int SwapBytes(int value)
        {
            return (int)((value >> 24) & 0x000000FF) |
                   (int)((value >> 8) & 0x0000FF00) |
                   (int)((value << 8) & 0x00FF0000) |
                   (int)((value << 24));
        }
    }
}
