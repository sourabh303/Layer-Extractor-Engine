using src_core.Services;

namespace src_core.Tests;

public class ActiveProjectStateTests
{
    [Fact]
    public void Constructor_InitializesEmpty()
    {
        var state = new ActiveProjectState();
        Assert.Empty(state.LayerMaskPaths);
    }

    [Fact]
    public void AddLayer_AddsNewLayer()
    {
        var state = new ActiveProjectState();
        state.AddLayer("layer1", "/tmp/path1.png");

        Assert.Single(state.LayerMaskPaths);
        Assert.Equal("/tmp/path1.png", state.LayerMaskPaths["layer1"]);
    }

    [Fact]
    public void AddLayer_UpdatesExistingLayer()
    {
        var state = new ActiveProjectState();
        state.AddLayer("layer1", "/tmp/path1.png");
        state.AddLayer("layer1", "/tmp/path2.png");

        Assert.Single(state.LayerMaskPaths);
        Assert.Equal("/tmp/path2.png", state.LayerMaskPaths["layer1"]);
    }

    [Fact]
    public void Clear_EmptiesDictionary()
    {
        var state = new ActiveProjectState();
        state.AddLayer("layer1", "/tmp/path1.png");
        state.AddLayer("layer2", "/tmp/path2.png");

        state.Clear();

        Assert.Empty(state.LayerMaskPaths);
    }
}
