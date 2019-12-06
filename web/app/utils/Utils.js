export function range(start, stop, step) {
    if (typeof stop == 'undefined') {
        // one param defined
        stop = start;
        start = 0;
    }

    if (typeof step == 'undefined') {
        step = 1;
    }

    if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) {
        return [];
    }

    var result = [];
    for (var i = start; step > 0 ? i < stop : i > stop; i += step) {
        result.push(i);
    }

    return result;
};

export const newMatrix = (m, n, defaultValue = 0) => {
    let matrix = [];
    for (let x = 0; x < m; x++) {
        let array = [];
        for (let y = 0; y < n; y++)
            array[y] = defaultValue;

        matrix[x] = array;
    }

    return matrix;
}

export const editDistance = (s1, s2) => {
    let m = s1.length;
    let n = s2.length;

    let dp = newMatrix(m + 1, n + 1);
    let bt = newMatrix(m + 1, n + 1);

    for (let i = 0; i <= m; i++)
        for (let j = 0; j <= n; j++) {
            if (i === 0) {
                dp[i][j] = j;
                bt[i][j] = 1;
            } else if (j === 0) {
                dp[i][j] = i;
                bt[i][j] = 2;
            } else if (s1.charAt(i - 1) === s2.charAt(j - 1)) {
                dp[i][j] = dp[i - 1][j - 1];
                bt[i][j] = 4;
            } else {
                let [back, mini] = findMin(dp[i][j - 1], dp[i - 1][j], dp[i - 1][j - 1]);
                dp[i][j] = mini + 1;
                bt[i][j] = back;
            }
        }

    let a = m, b = n, s1x = "", mid = "", s2x = "";
    console.log(bt, dp);

    while (a >= 0 && b >= 0) {
        let move = bt[a][b];

        if (move === 1) {
            if (b > 0) {
                s1x = '-' + s1x;
                mid = ' ' + mid;
                s2x = s2.charAt(b - 1) + s2x;
            }

            b -= 1;
        }
        if (move === 2) {
            if (a > 0) {
                s1x = s1.charAt(a - 1) + s1x;
                mid = ' ' + mid;
                s2x = '-' + s2x;
            }

            a -= 1;
        }
        if (move === 3) {
            if (b > 0 && a > 0) {
                s1x = s1.charAt(a - 1) + s1x;
                mid = ' ' + mid;
                s2x = s2.charAt(b - 1) + s2x;
            }

            a -= 1;
            b -= 1;
        }
        if (move === 4) {
            if (b > 0 && a > 0) {
                s1x = s1.charAt(a - 1) + s1x;
                mid = '|' + mid;
                s2x = s2.charAt(b - 1) + s2x;
            }

            a -= 1;
            b -= 1;
        }
    }

    console.log(dp[m][n]);

    return [s1x, mid, s2x];
}

const findMin = (insert, dell, mismatch) => {
    if (insert <= dell) {
        if (insert <= mismatch)
            return [1, insert];

        return [3, mismatch];
    } else if (mismatch <= dell) {
        return [3, mismatch];
    }

    return [2, dell];
};
