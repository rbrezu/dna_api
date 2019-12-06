import React from 'react';
import Button from "react-bootstrap/Button";
import history from '../history';
import TableComponent from "../component/TableComponent";

class Sequence extends React.Component {

    constructor(props) {
        super(props);
    }

    render() {
        return <div className="container" style={{marginTop: 75, marginBottom: 250}}>
            <div className='mb-5 flex d-flex justify-content-between align-center'>
                <Button variant="primary" onClick={() => this.table._resetFilters()}>Reset Filters</Button>
                <div>
                    {/*<Button variant="danger" onClick={() => this.table._deleteSelected()}>Delete*/}
                    {/*    Selected</Button>*/}
                    <Button className={'ml-2'} variant="success" onClick={() => history.push('/sequence/upload')}>Upload</Button>
                </div>
            </div>
            <TableComponent
                ref={ref => this.table = ref}
                columns={[
                    {
                        dataField: 'sequence_id',
                        text: 'Name',
                        formatter: (cell, row, rowIndex) => <a href={`/sequence/${cell}`}>{cell}</a>,
                        filter: {field: 'sequence_id', type: 'text'}
                    },
                    {
                        dataField: 'tags',
                        text: 'Tags',
                        filter: {field: 'tags', type: 'text'}
                    },
                    {
                        dataField: 'sequence_size',
                        text: 'Size',
                        sort: true,
                        // filter: {field: 'sequence_size', type: 'text'}
                    },
                    {
                        dataField: 'last_modified_date',
                        text: 'Last Modified Date',
                        sort: true
                    }
                ]}
                tableType={'sequence'}
            />
        </div>
    }
}

export default Sequence;
