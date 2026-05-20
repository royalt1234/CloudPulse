import { PublicClientApplication } from "@azure/msal-browser";

export const msalConfig = {
    auth: {
        clientId: import.meta.env.VITE_AZURE_CLIENT_ID,
        authority: `https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_TENANT_ID}`,
        redirectUri: "/",
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false,
    }
};

export const loginRequest = {
    scopes: ["User.Read"]
};

export const msalInstance = new PublicClientApplication(msalConfig);

let instance;
try {
    instance = new PublicClientApplication(msalConfig);
} catch (err) {
    console.error("Failed to create PublicClientApplication:", err);
    // Create a mock instance so the bundle doesn't crash on import,
    // safely propagating the error to the main initialization promise instead!
    instance = {
        initialize: () => Promise.reject(err),
        loginRedirect: () => Promise.reject(err),
        handleRedirectPromise: () => Promise.resolve(null),
        getAllAccounts: () => [],
        addEventCallback: () => {}
    };
}