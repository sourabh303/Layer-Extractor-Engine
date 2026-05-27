namespace Models
{

    public partial class ExportRequest
    {
        /// <summary>
        /// The absolute path to the destination folder chosen by the user
        /// </summary>
        public string DestinationFolder { get; set; }

        /// <summary>
        /// An array of requested export formats
        /// </summary>
        public Format[] Formats { get; set; }
    }

    public enum Format { Png, Psd, Svg, TiffCmyk, TiffRgb };
}
