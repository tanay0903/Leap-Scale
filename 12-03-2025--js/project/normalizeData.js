const fs = require("fs");
const Fuse = require("fuse.js"); // Ensure proper import

// Load configuration file
const config = JSON.parse(fs.readFileSync("senso_config.json", "utf8"));

// Create mapping object for fuzzy search
const fuseOptions = { threshold: 0.3, keys: ["aliases"] };
const fuseIndex = {};

for (const key in config) {
    fuseIndex[key] = new Fuse(config[key].map(alias => ({ key, aliases: alias })), fuseOptions);
}

// Function to normalize JSON keys
function normalizeJson(data) {
    const normalizedData = {};

    for (const key in data) {
        const result = fuseIndex[key]?.search(key);
        const normalizedKey = result?.length ? result[0].item.key : key;
        
        // Recursively normalize nested objects
        if (Array.isArray(data[key])) {
            normalizedData[normalizedKey] = data[key].map(item => normalizeJson(item));
        } else if (typeof data[key] === "object" && data[key] !== null) {
            normalizedData[normalizedKey] = normalizeJson(data[key]);
        } else {
            normalizedData[normalizedKey] = data[key];
        }
    }

    return normalizedData;
}

module.exports = { normalizeJson };
