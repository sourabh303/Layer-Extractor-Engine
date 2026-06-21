using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using SkiaSharp;

namespace src_core.Services;

/// <summary>
/// Minimal custom PSD Writer for 8-bit RGB layers.
/// Does not implement full PSD spec, only sufficient structures to
/// group SkiaSharp pixel buffers into layers preserving hierarchy.
/// </summary>
public static class PsdWriter
{
    public static void Write(string outputPath, int width, int height, List<(string Name, SKBitmap Bitmap)> layers)
    {
        using var fs = new FileStream(outputPath, FileMode.Create, FileAccess.Write);
        using var writer = new BinaryWriter(fs);

        // 1. File Header
        writer.Write(Encoding.ASCII.GetBytes("8BPS")); // Signature
        writer.Write(SwapBytes((short)1)); // Version
        writer.Write(new byte[6]); // Reserved
        writer.Write(SwapBytes((short)3)); // Channels (3 = RGB)
        writer.Write(SwapBytes((int)height));
        writer.Write(SwapBytes((int)width));
        writer.Write(SwapBytes((short)8)); // Depth
        writer.Write(SwapBytes((short)3)); // ColorMode (3 = RGB)

        // 2. Color Mode Data
        writer.Write(SwapBytes((int)0)); // Length (0 for RGB)

        // 3. Image Resources
        // Write empty image resources block
        writer.Write(SwapBytes((int)0));

        // 4. Layer and Mask Information
        WriteLayerAndMaskInfo(writer, width, height, layers);

        // 5. Image Data (Composite)
        // For our minimal implementation, we write an empty composite image.
        // Modern Photoshop reads the layers block to reconstruct.
        writer.Write(SwapBytes((short)0)); // 0 = Raw

        // Write raw composite (black/empty)
        int compositeSize = width * height * 3;
        writer.Write(new byte[compositeSize]);
    }

    private static void WriteLayerAndMaskInfo(BinaryWriter writer, int width, int height, List<(string Name, SKBitmap Bitmap)> layers)
    {
        // We need to calculate sizes first or use a memory stream
        using var layerInfoStream = new MemoryStream();
        using var layerWriter = new BinaryWriter(layerInfoStream);

        // Write Layer Info
        WriteLayerInfo(layerWriter, width, height, layers);

        // Global layer mask info (empty)
        layerWriter.Write((int)0);

        // Write the total length of Layer and Mask Information section
        long totalLength = layerInfoStream.Length;
        // Pad to even length
        if (totalLength % 2 != 0)
        {
            layerWriter.Write((byte)0);
            totalLength++;
        }

        writer.Write(SwapBytes((int)totalLength));
        writer.Write(layerInfoStream.ToArray());
    }

    private static void WriteLayerInfo(BinaryWriter writer, int width, int height, List<(string Name, SKBitmap Bitmap)> layers)
    {
        using var layerRecordsStream = new MemoryStream();
        using var recordsWriter = new BinaryWriter(layerRecordsStream);

        // Count
        recordsWriter.Write(SwapBytes((short)-layers.Count)); // Negative means first alpha channel contains transparency

        // Write layer records
        foreach (var layer in layers)
        {
            // Rectangle (Top, Left, Bottom, Right)
            recordsWriter.Write(SwapBytes((int)0));
            recordsWriter.Write(SwapBytes((int)0));
            recordsWriter.Write(SwapBytes((int)height));
            recordsWriter.Write(SwapBytes((int)width));

            // Number of channels (4: R, G, B, A)
            recordsWriter.Write(SwapBytes((short)4));

            // Channel info (ID, Length) -> -1=A, 0=R, 1=G, 2=B
            // Length = 2 bytes (compression format) + (width * height) for raw
            int channelDataLength = 2 + (width * height);

            recordsWriter.Write(SwapBytes((short)-1)); // Alpha
            recordsWriter.Write(SwapBytes((int)channelDataLength));

            recordsWriter.Write(SwapBytes((short)0)); // R
            recordsWriter.Write(SwapBytes((int)channelDataLength));

            recordsWriter.Write(SwapBytes((short)1)); // G
            recordsWriter.Write(SwapBytes((int)channelDataLength));

            recordsWriter.Write(SwapBytes((short)2)); // B
            recordsWriter.Write(SwapBytes((int)channelDataLength));

            recordsWriter.Write(Encoding.ASCII.GetBytes("8BIM")); // Blend mode sig
            recordsWriter.Write(Encoding.ASCII.GetBytes("norm")); // Blend mode key
            recordsWriter.Write((byte)255); // Opacity
            recordsWriter.Write((byte)0); // Clipping
            recordsWriter.Write((byte)1); // Flags (Bit 1 = visible)
            recordsWriter.Write((byte)0); // Filler

            // Extra data length
            using var extraDataStream = new MemoryStream();
            using var extraWriter = new BinaryWriter(extraDataStream);

            // Layer mask data (empty)
            extraWriter.Write(SwapBytes((int)0));

            // Layer blending ranges (empty)
            extraWriter.Write(SwapBytes((int)0));

            // Layer name (Pascal string, padded to multiple of 4)
            string name = layer.Name.Length > 255 ? layer.Name.Substring(0, 255) : layer.Name;
            extraWriter.Write((byte)name.Length);
            extraWriter.Write(Encoding.ASCII.GetBytes(name));

            // Pad to multiple of 4
            int nameLength = 1 + name.Length;
            while (nameLength % 4 != 0)
            {
                extraWriter.Write((byte)0);
                nameLength++;
            }

            recordsWriter.Write(SwapBytes((int)extraDataStream.Length));
            recordsWriter.Write(extraDataStream.ToArray());
        }

        // Write Channel Image Data for all layers
        foreach (var layer in layers)
        {
            // Extract channels
            byte[] a = new byte[width * height];
            byte[] r = new byte[width * height];
            byte[] g = new byte[width * height];
            byte[] b = new byte[width * height];

            // ⚡ Bolt Optimization: Use fast unsafe byte extraction based on known color formats.
            // Avoids O(W*H) overhead of `layer.Bitmap.GetPixel(x, y)` which is exceptionally slow.
            unsafe
            {
                int totalPixels = width * height;
                // Only use the fast unsafe path if we know the row bytes match perfectly (no padding)
                if ((layer.Bitmap.ColorType == SKColorType.Bgra8888 || layer.Bitmap.ColorType == SKColorType.Rgba8888) &&
                    layer.Bitmap.RowBytes == width * 4)
                {
                    byte* ptr = (byte*)layer.Bitmap.GetPixels().ToPointer();
                    bool isBgra = layer.Bitmap.ColorType == SKColorType.Bgra8888;

                    for (int i = 0; i < totalPixels; i++)
                    {
                        if (isBgra)
                        {
                            b[i] = ptr[i * 4];
                            g[i] = ptr[i * 4 + 1];
                            r[i] = ptr[i * 4 + 2];
                            a[i] = ptr[i * 4 + 3];
                        }
                        else
                        {
                            r[i] = ptr[i * 4];
                            g[i] = ptr[i * 4 + 1];
                            b[i] = ptr[i * 4 + 2];
                            a[i] = ptr[i * 4 + 3];
                        }
                    }
                }
                else
                {
                    // Fallback for other formats or if there is row padding
                    ReadOnlySpan<SKColor> pixels = layer.Bitmap.Pixels;
                    for (int i = 0; i < totalPixels; i++)
                    {
                        var color = pixels[i];
                        a[i] = color.Alpha;
                        r[i] = color.Red;
                        g[i] = color.Green;
                        b[i] = color.Blue;
                    }
                }
            }

            // Write Alpha
            recordsWriter.Write(SwapBytes((short)0)); // Raw compression
            recordsWriter.Write(a);

            // Write Red
            recordsWriter.Write(SwapBytes((short)0));
            recordsWriter.Write(r);

            // Write Green
            recordsWriter.Write(SwapBytes((short)0));
            recordsWriter.Write(g);

            // Write Blue
            recordsWriter.Write(SwapBytes((short)0));
            recordsWriter.Write(b);
        }

        long recordsLength = layerRecordsStream.Length;
        // Pad to even length
        if (recordsLength % 2 != 0)
        {
            recordsWriter.Write((byte)0);
            recordsLength++;
        }

        writer.Write(SwapBytes((int)recordsLength));
        writer.Write(layerRecordsStream.ToArray());
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
