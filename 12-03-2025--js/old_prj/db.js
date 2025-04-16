const mysql = require("mysql2");

const pool = mysql.createPool({
    host: "localhost",
    user: "root", 
    password: "1234", 
    database: "iot_data"
}).promise();

async function saveToDatabase(deviceId, temperature, unit, timestamp) {
    try {
        const query = `
            INSERT INTO sensor_reading (deviceId, temperature, unit, timestamp) 
            VALUES (?, ?, ?, ?)
        `;
        await pool.execute(query, [deviceId, temperature, unit, timestamp]);
        console.log("✅ Data stored in MySQL:", { deviceId, temperature, unit, timestamp });
    } catch (error) {
        console.error("❌ Database Error:", error);
    }
}

module.exports = { saveToDatabase };
