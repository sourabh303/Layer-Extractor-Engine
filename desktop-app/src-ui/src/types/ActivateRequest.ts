export interface ActivateRequest {
    /**
     * The Supabase JWT returned upon successful login.
     */
    jwt: string;
    /**
     * The unique hardware identifier of the machine.
     */
    machine_id: string;
    [property: string]: unknown;
}
