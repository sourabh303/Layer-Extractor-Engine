export interface ExportRequest {
    /**
     * The absolute path to the destination folder chosen by the user
     */
    destination_folder: string;
    /**
     * An array of requested export formats
     */
    formats: Format[];
    [property: string]: any;
}

export enum Format {
    PNG = "PNG",
    Psd = "PSD",
    SVG = "SVG",
    TiffCmyk = "TIFF_CMYK",
    TiffRGB = "TIFF_RGB",
}
