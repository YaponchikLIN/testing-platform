interface NWFileSystem {
    readDir(path: string): Promise<string[]>;
    stat(path: string): Promise<{ size: number }>;
    exists(path: string): Promise<boolean>;
}

interface NWGui {
    App: {
        data: {
            settings?: any;
            [key: string]: any;
        };
    };
}

declare global {
    interface Window {
        nw: {
            fs: NWFileSystem;
            Store: any;
            require: (module: string) => any;
            gui?: NWGui;
        };
    }
}