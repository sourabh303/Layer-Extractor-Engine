export interface ExportRequest {
    /**
     * The absolute path to the destination folder chosen by the user
     */
    destination_folder: string;
    /**
     * An array of requested export formats
     */
    formats: Format[];
    [property: string]: unknown;
}

export type Format =
    | "PNG"
    | "PSD"
    | "SVG"
    | "TIFF_CMYK"
    | "TIFF_RGB";

export const Format = {
    PNG: "PNG" as const,
    Psd: "PSD" as const,
    SVG: "SVG" as const,
    TiffCmyk: "TIFF_CMYK" as const,
    TiffRGB: "TIFF_RGB" as const,
};
