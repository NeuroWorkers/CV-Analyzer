import config from '../../../config.json'; 

export const globalConfig = {
    basenameFrontend: config['basename-frontend'],
    domain: (config.domain === "") ? window.location.hostname : config.domain,
    port: config.port,
    apiPath: config['api-path'],
    get defaultList() {
        return this.port.length > 0 
            ? [
                `${this.domain}:${this.port}`,
                `${this.domain}/${this.apiPath}`
            ]
            : [
                `${this.domain}/${this.apiPath}`
            ];
    },
    backendCheckToPath: config['backend-check-to-path']
};