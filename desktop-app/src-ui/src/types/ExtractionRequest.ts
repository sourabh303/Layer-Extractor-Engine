export interface ExtractionRequest {
    /**
     * The absolute path to the source image file
     */
    source_path: string;
    [property: string]: unknown;
}

export interface ExtractionMetadataResponse {
    bboxes:                Array<number[]>;
    hardware_mode_used:    string;
    layers_extracted:      number;
    localized_coordinates: LocalizedCoordinate[];
    message:               string;
    output_paths:          string[];
    source_path:           string;
    status:                string;
    [property: string]: unknown;
}

export interface LocalizedCoordinate {
    height: number;
    width:  number;
    x:      number;
    y:      number;
    [property: string]: unknown;
}
