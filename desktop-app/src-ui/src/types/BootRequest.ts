export interface BootRequest {
    /**
     * The Supabase JWT to verify for boot authorization.
     */
    jwt: string;
    /**
     * The unique hardware identifier of the machine.
     */
    machine_id: string;
    [property: string]: unknown;
}
