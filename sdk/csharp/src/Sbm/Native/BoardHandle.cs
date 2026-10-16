using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>Owns an sbm_board of the core and frees it exactly once (kern-c-schnittstelle.md).</summary>
internal sealed class BoardHandle : SafeHandle
{
    public BoardHandle()
        : base(IntPtr.Zero, ownsHandle: true) { }

    public override bool IsInvalid => handle == IntPtr.Zero;

    protected override bool ReleaseHandle()
    {
        Core.sbm_board_free(handle);
        return true;
    }
}
