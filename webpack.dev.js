const path = require('path');
const webpack = require('webpack');
const ExtractTextPlugin = require("extract-text-webpack-plugin");
const AssetsPlugin = require('assets-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin')
const BrowserSyncPlugin = require('browser-sync-webpack-plugin');
const SimpleProgressWebpackPlugin = require('simple-progress-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin')
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

let pathsToClean = [
    'dist/*',
]

let cleanOptions = {
    verbose: true,
    dry: false
}

var SRC = path.resolve(__dirname, 'src/images');

var extractPlugin = new ExtractTextPlugin('main-bundle-[hash].css');

module.exports = {
    mode: 'development',
    devtool: 'source-map',
    entry: {
        main: "./web/app/index.js"
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        publicPath: "/dist/",
        filename: '[name]-bundle-[hash].js'
    },
    resolve: {
        extensions: [
            '.jsx', '.js', '.json'
        ],
        modules: [
            'node_modules',
            path.resolve(__dirname, './node_modules')
        ]
    },
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: [/node_modules/],
                use: [
                    {
                        loader: 'babel-loader',
                        // options: {
                        //     "presets": ["es2015", "stage-0", "react"]
                        // }
                    }
                ],
            },
            // {
            //     test: /\.(jpe?g|png|mp3)$/i,
            //     //  include: SRC,
            //     loaders: ['file-loader']
            // },
            {
                test: /\.(gif|png|jpe?g|svg)$/i,
                use: [
                    'file-loader',
                    {
                        loader: 'image-webpack-loader',
                        options: {
                            bypassOnDebug: true, // webpack@1.x
                            disable: true, // webpack@2.x and newer
                        },
                    },
                ],
            },
            {
                test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                //include: SRC,
                use: [
                    {
                        loader: 'url-loader',
                        options: {
                            limit: 1000,
                            mimetype: 'application/font-woff'
                        }
                    }

                ]
            },
            {test: /\.(ttf|eot|svg|gif)(\?v=[0-9]\.[0-9]\.[0-9])?$/, loader: 'url-loader?limit=100000'},
            {
                test: /\.css|\.scss|\.sass$/,
                //exclude: [/node_modules/],
                use: [
                    {
                        loader: "style-loader" // creates style nodes from JS strings
                    },
                    {
                        loader: "css-loader" // translates CSS into CommonJS
                    },
                    // {
                    //     loader: "postcss-loader"
                    // },
                    {
                        loader: "sass-loader" // compiles Sass to CSS
                    },

                ]
            }
        ]
    },
    devServer: {
        contentBase: './dist/',
        proxy: [{
            context: [
                '/'
            ],
            target: `http://localhost:8888`,
            secure: false,
        }],
        port: 9000,
        historyApiFallback: true,
        // stats: options.stats,
        watchOptions: {
            ignored: /node_modules/
        },
        // https: options.tls
    },
    plugins: [
        new CleanWebpackPlugin(pathsToClean, cleanOptions),
        new CopyWebpackPlugin([
            {
                from: 'public/favicon.ico',
                to: 'favicon.ico',
                toType: 'file'
            },
            {
                from: 'public/manifest.json',
                to: 'manifest.json',
                toType: 'file'
            },
            {from: 'web/assets/scripts', to: 'assets/scripts'},
            // {from: 'web/assets/fonts', to: 'assets/fonts'}
        ]),
        new SimpleProgressWebpackPlugin({
            format: 'compact'
        }),
        new BrowserSyncPlugin({
            host: 'localhost',
            port: 9000,
            proxy: {
                target: `http://localhost:9060`,
                proxyOptions: {
                    changeOrigin: false  //pass the Host header to the backend unchanged  https://github.com/Browsersync/browser-sync/issues/430
                }
            },
            socket: {
                clients: {
                    heartbeatTimeout: 60000
                }
            }
        }, {
            reload: false
        }),
        new webpack.HotModuleReplacementPlugin(),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery"
        }),


        // new webpack.optimize.UglifyJsPlugin(),
        extractPlugin,

        new HtmlWebpackPlugin({
            title: 'Framework',
            template: 'public/index.html'
        }),
        new AssetsPlugin()
    ]
};
