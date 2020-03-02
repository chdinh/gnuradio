/*
 * Copyright 2020 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

/* This file is automatically generated using bindtool */

#include <pybind11/pybind11.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/digital/mpsk_snr_est_cc.h>

void bind_mpsk_snr_est_cc(py::module& m)
{
    using mpsk_snr_est_cc    = gr::digital::mpsk_snr_est_cc;


    py::class_<mpsk_snr_est_cc,gr::sync_block,
        std::shared_ptr<mpsk_snr_est_cc>>(m, "mpsk_snr_est_cc")

        .def(py::init(&mpsk_snr_est_cc::make),
           py::arg("type"), 
           py::arg("tag_nsamples") = 10000, 
           py::arg("alpha") = 0.001 
        )
        

        .def("snr",&mpsk_snr_est_cc::snr)
        .def("type",&mpsk_snr_est_cc::type)
        .def("tag_nsample",&mpsk_snr_est_cc::tag_nsample)
        .def("alpha",&mpsk_snr_est_cc::alpha)
        .def("set_type",&mpsk_snr_est_cc::set_type,
            py::arg("t") 
        )
        .def("set_tag_nsample",&mpsk_snr_est_cc::set_tag_nsample,
            py::arg("n") 
        )
        .def("set_alpha",&mpsk_snr_est_cc::set_alpha,
            py::arg("alpha") 
        )
        .def("to_basic_block",[](std::shared_ptr<mpsk_snr_est_cc> p){
            return p->to_basic_block();
        })
        ;


} 