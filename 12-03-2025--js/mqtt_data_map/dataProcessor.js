// const moment = require("moment");
// const pool = require("./database");

// const synonyms = {
//     temp: "temperature",
//     tempVal: "temperature",
//     tempCelsius: "temperature",
//     tempFahrenheit: "temperature",
//     tempKelvin: "temperature",
//     timestamp: "time",
//     ts: "time",
//     tstamp: "time",
//     t: "time",

    
//     Temp: "temperature",
//     TempVal: "temperature",
//     TempCelsius: "temperature",
//     TempFahrenheit: "temperature",
//     TempKelvin: "temperature",
//     Timestamp: "time",
//     Ts: "time",
//     Tstamp: "time",
//     T: "time"
// };

// function normalizeData(rawData) {
//     let data = JSON.parse(rawData);

//     // Apply ontology mapping
//     let normalizedData = {};
//     for (let key in data) {
//         let mappedKey = synonyms[key] || key;
//         normalizedData[mappedKey] = data[key];
//     }

//     // Ensure unit is mapped before conversion
//     let unit = normalizedData.unit || data.unit;

//     // Convert Fahrenheit to Celsius
//     if (normalizedData.temperature && unit === "F") {
//         normalizedData.temperature = ((normalizedData.temperature - 32) * 5) / 9;
//         normalizedData.unit = "C";
//     }

//     // Convert Kelvin to Celsius
//     if (normalizedData.temperature && unit === "K") {
//         normalizedData.temperature = normalizedData.temperature - 273.15;
//         normalizedData.unit = "C";
//     }

//     // Standardize timestamp format
//     if (!normalizedData.time || normalizedData.time.trim() === "") {
//         normalizedData.time = moment().utc().toISOString(); // Assign current ISO 8601 time if blank
//     } else if (!isNaN(normalizedData.time) && normalizedData.time.toString().length >= 10) {
//         const epochTime = Number(normalizedData.time);
//         normalizedData.time = moment.utc(epochTime * 1000).toISOString(); // Convert epoch time (seconds) to UTC ISO 8601
//         // normalizedData.formattedTime = moment.utc(epochTime * 1000).format("HH:mm:ss"); // Convert to HH:mm:ss format
//     } else {
//         normalizedData.time = moment.utc(normalizedData.time, moment.ISO_8601, true).isValid()
//             ? moment.utc(normalizedData.time).toISOString()
//             : moment().utc().toISOString(); // If invalid, assign current ISO 8601 time
//     }

//     return normalizedData;
// }

// // Function to store data in MySQL
// // async function storeDataInMySQL(normalizedData) {
// //     try {
// //         const sql = `INSERT INTO sensor_readings (device_id, temperature, unit, time) VALUES (?, ?, ?, ?)`;
// //         const mysqlDatetime = moment.utc(normalizedData.time).toISOString();
// //         //console.log("MySQL Datetime:", mysqlDatetime);
// //         const values = [normalizedData.deviceId, normalizedData.temperature, normalizedData.unit, mysqlDatetime];
// //         await pool.query(sql, values);
// //         console.log("✅ Data stored in MySQL:", normalizedData);
// //     } catch (err) {
// //         console.error("❌ Error inserting data into MySQL:", err);
// //     }
// // }

// async function storeDataInMySQL(normalizedData, rawData) {
//     try {
//         let { device_id, temperature, unit, time } = normalizedData;

//         // 🔍 Debugging Log
//         console.log("🛠️ Debugging: Data before inserting into MySQL:", {device_id, temperature, unit, time, rawData });

//         // Ensure all required fields are properly set
//         device_id = device_id || null;
//         temperature = temperature !== undefined ? temperature : null;
//         unit = unit || null;
//         time = time || moment().utc().toISOString(); // Default to current UTC time if missing
//         rawData = rawData && rawData.trim() !== "" ? rawData : JSON.stringify(normalizedData);

//         if (temperature === null || unit === null || time === null) {
//             console.error("❌ Missing required data. Skipping insert:", { device_id, temperature, unit, time });
//             return;
//         }

//         // 🔹 Store Raw Data (Allowing NULL device_id)
//         console.log("📤 Storing raw data...");
//         await pool.execute(
//             "INSERT INTO raw_sensor_data (device_id, raw_payload, received_time) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE raw_payload = VALUES(raw_payload), received_time = VALUES(received_time)",
//             [device_id, rawData, time]
//         );
//         console.log("✅ Raw data stored successfully");

//         // 🔹 If `device_id` is null, store in a generic table
//         if (!device_id) {
//             console.log("📤 Storing in generic table...");
//             await pool.execute(
//                 `INSERT INTO normalized_device_data (device_id, temperature, unit, time) VALUES (?, ?, ?, ?) 
//                 ON DUPLICATE KEY UPDATE temperature = VALUES(temperature), unit = VALUES(unit), time = VALUES(time)`,
//                 [device_id, temperature, unit, time]
//             );
//             console.log("✅ Data stored in generic table");
//             return;
//         }

//         // 🔹 Create Device-Specific Table if not exists
//         const deviceTable = `device_${device_id}`;
//         console.log(`📤 Creating table if not exists: ${deviceTable}`);
//         await pool.execute(
//             `CREATE TABLE IF NOT EXISTS ${deviceTable} (
//                 id INT AUTO_INCREMENT PRIMARY KEY,
//                 temperature FLOAT NOT NULL,
//                 unit VARCHAR(10) NOT NULL,
//                 time VARCHAR(30) NOT NULL
//             )`
//         );

//         // 🔹 Insert Data into Device-Specific Table
//         console.log(`📤 Inserting data into ${deviceTable}...`);
//         await pool.execute(
//             `INSERT INTO ${deviceTable} (temperature, unit, time) VALUES (?, ?, ?)`,
//             [temperature, unit, time]
//         );

//         console.log(`✅ Processed data for device: ${device_id}`);
//     } catch (error) {
//         console.error("❌ Error processing data:", error);
//     }
// }


// module.exports = { normalizeData, storeDataInMySQL};
