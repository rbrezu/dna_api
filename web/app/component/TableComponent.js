import React from "react";
import axios from "axios";
import Button from "react-bootstrap/Button";
import history from "../history";
import BootstrapTable from "react-bootstrap-table-next";
import paginationFactory from "react-bootstrap-table2-paginator";

import filterFactory, {textFilter} from 'react-bootstrap-table2-filter';


class TableComponent extends React.Component {

    constructor(props) {
        super(props);
        this.columns = this.props.columns;
        this.filters = {};
        this.state = {
            loading: true,
            items: [],
            totalSize: 0,
            selected: [],
            columns: this._makeColumns(this.columns),
            defaultSorted: [{
                dataField: 'last_modified_date',
                order: 'desc'
            }],
            sizePerPage: 10,
            page: 1
        }
    }

    _createFilter = (field, type) => {
        console.log(this.state);

        const defaultValue = this.state && this.state._query
            && this.state._query[field] && this.state._query[field]['$regex'];

        let filter;
        if (type === 'text')
            filter = textFilter;

        return filter({
            defaultValue,
            getFilter: (filter) => this.filters[field] = filter
        });
    };

    _makeColumns = (columns) => {
        console.log(columns);
        // {
        //     dataField: '_id',
        //         text: 'id',
        //     formatter: (cell, row, rowIndex) => <a href={`/${this.props.tableType}/${cell}`}>{cell}</a>
        // },
        let cols = [
            ...columns.map(column => ({
                ...column,
                filter: column.filter ? this._createFilter(column.filter.field, column.filter.type) : undefined
            }))
        ]

        console.log(columns.map(column => ({
            ...column,
            filter: column.filter && this._createFilter(column.filter.field, column.filter.type)
        })))

        console.log(cols);

        return cols;
    };

    _resetFilters = () => {
        Object.keys(this.filters).forEach(key => this.filters[key](''));
        this.setState({_query: undefined, loading: true},
            () => this._getItems());
    };

    componentDidMount() {
        const oldState = JSON.parse(localStorage.getItem(this.props.tableType));
        console.log(oldState);

        this.setState(oldState,
            () => this.setState({columns: this._makeColumns(this.columns)},
                () => this._getItems()));

        // keeping the window to call componentCleanup on page refresh
        window.addEventListener('beforeunload', this.componentCleanup);
    }

    componentWillUnmount() {
        this.componentCleanup();
        window.removeEventListener('beforeunload', this.componentCleanup);
    }

    componentCleanup = () => {
        const {sizePerPage, page, sort, selected, _query} = this.state;
        localStorage.setItem(this.props.tableType, JSON.stringify({sizePerPage, page, sort, selected, _query}));
    };

    _getItems = () => {
        const [limit, skip] = [this.state.sizePerPage, (this.state.page - 1) * this.state.sizePerPage];
        const {sort, _query} = this.state;

        axios.get(`/api/crud/${this.props.tableType}`, {params: {limit, skip, sort, _query}})
            .then((response) => {
                console.log(response.headers)
                this.setState({
                    items: response.data,
                    loading: false,
                    totalSize: parseInt(response.headers['x-total-count'])
                });
            })
    }

    _deleteSelected = () => {
        axios.delete(`/api/crud/${this.props.tableType}`, {params: {_query: {'_id': {'$in': this.state.selected}}}})
            .then((response) => {
                this._getItems();
            })
    }

    _onTableChanged = (type, data) => {
        console.log(type);
        switch (type) {
            case 'pagination':
                let {page, sizePerPage} = data;
                page = sizePerPage !== this.state.sizePerPage ? 1 : page;
                this.setState({page, sizePerPage, loading: true}, () => this._getItems());
                break;
            case 'sort':
                const {sortField, sortOrder} = data;
                this.setState({page: 1, sort: `${sortField},${sortOrder}`, loading: true}, () => this._getItems());
                break;
            case 'filter':
                const {filters} = data;
                const query = {};
                Object.keys(filters).forEach((field) => {
                    const {filterVal, filterType, comparator} = filters[field];
                    switch (filterType) {
                        case 'TEXT':
                            query[field] = {'$regex': filterVal, '$options': 'i'};
                            break;
                    }

                });
                this.setState({_query: query, loading: true, page: 1}, () => this._getItems());

                break;
        }
    }

    render() {
        const {page, sizePerPage, items, columns, totalSize, selected} = this.state;

        return <div className="container">
            <div>Total count: {totalSize}</div>
            <BootstrapTable
                bootstrap4
                remote={{sort: true, filter: true, pagination: true}}
                onTableChange={this._onTableChanged}
                striped
                hover
                keyField='_id'
                // selectRow={{
                //     mode: 'checkbox',
                //     // clickToSelect: true,
                //     selected: [...selected],
                //     onSelect: (row, isSelect, rowIndex, e) => {
                //         console.log(row, isSelect, rowIndex, e, this.state.selected);
                //         if (isSelect) {
                //             if (selected.indexOf(row._id) === -1)
                //                 this.setState({selected: [...selected, row._id]});
                //         } else this.setState({selected: selected.filter(x => x !== row._id)});
                //
                //         return true;
                //     },
                //     onSelectAll: (isSelect, rows, e) => {
                //         if (isSelect) {
                //             this.setState({
                //                 selected: [
                //                     ...selected,
                //                     ...rows.filter(row => !selected.find(row_id => row._id === row_id)).map(row => row._id)
                //                 ]
                //             });
                //         } else this.setState({selected: selected.filter(row_id => !rows.find(row => row._id === row_id))});
                //     }
                // }}
                pagination={paginationFactory({
                    page, sizePerPage, totalSize,
                    sizePerPageList: [{
                        text: '5th', value: 5
                    }, {
                        text: '10th', value: 10
                    }, {
                        text: 'All', value: totalSize
                    }]
                })}
                filter={filterFactory()}
                data={items}
                columns={columns}/>
            {this.state.loading && <div className={'overlay loading'}/>}
        </div>
    }

}

export default TableComponent;
