const fs = require("fs");
const Fuse = require("fuse.js");

const config = JSON.parse(fs.readFileSync("./config/sen_config.json", "utf-8"));


function normalizeKey(key) {
    for (const standardKey in config) {
        const fuse = new Fuse(config[standardKey], { includeScore: true, threshold: 0.3 });
        const result = fuse.search(key);
        if (result.length > 0) {
            return standardKey; 
        }
    }
    return key; 
}

// Function to normalize an entire JSON object
function normalizeJson(obj) {
    if (Array.isArray(obj)) {
        return obj.map(normalizeJson);
    } else if (typeof obj === "object" && obj !== null) {
        return Object.fromEntries(
            Object.entries(obj).map(([key, value]) => [
                normalizeKey(key),
                normalizeJson(value)
            ])
        );
    }
    return obj;
}

module.exports = { normalizeJson };
