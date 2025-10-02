interface Device {
    name: string;
    quantity: number;
    macPerDevice: number;
    totalMacs: number;
    macList: Record<string, string[]>;
}

interface Order {
    name: string;
    uuid: string;
    date: string;
    status: string;
}

interface OperationResult {
    success: boolean;
    message?: string;
}