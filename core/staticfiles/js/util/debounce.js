function debounce(func, delay = 800) {
    let timer;
    return (...args) => {
        // Clear the previous timer if the user is still typing
        clearTimeout(timer);
        
        // Start a new timer
        timer = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}


// how to use

// const inputField = document.getElementById('myInput');

// // 1. Define the function that talks to the database
// function saveToDatabase(event) {
//     const value = event.target.value;
//     console.log("Saving to database:", value);
//     // Perform your fetch/axios request here
// }

// // 2. Wrap it in the debounce function
// const debouncedSave = debounce(saveToDatabase, 800);

// // 3. Attach it to the 'input' event
// inputField.addEventListener('input', debouncedSave);