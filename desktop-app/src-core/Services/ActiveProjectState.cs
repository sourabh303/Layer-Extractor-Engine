using System.Collections.Concurrent;

namespace src_core.Services;

/// <summary>
/// Minimal state management simulating the Active Project.
/// Holds references to the temporary masks stored on disk by the Python service.
/// </summary>
public class ActiveProjectState
{
    // Mocking an active project state that maps layer IDs to their temp PNG file paths.
    public ConcurrentDictionary<string, string> LayerMaskPaths { get; } = new();

    public void AddLayer(string layerId, string path)
    {
        LayerMaskPaths[layerId] = path;
    }

    public void Clear()
    {
        LayerMaskPaths.Clear();
    }
}
